#   Foremast - Pipeline Tooling
#
#   Copyright 2020 Redbox Automated Retail, LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""GCP IAM Policy management"""

import logging

import googleapiclient.discovery

LOG = logging.getLogger(__name__)


def get_policy(credentials, project_id):
    """Gets IAM policy for a project."""

    service = googleapiclient.discovery.build(
        "cloudresourcemanager", "v1", credentials=credentials,
        cache_discovery=False
    )
    policy = (
        service.projects()
        .getIamPolicy(
            resource=project_id,
            # Request policy version 3 to ensure conditional bindings are included
            # https://cloud.google.com/iam/docs/policies
            body={"options": {"requestedPolicyVersion": 3}},
        )
        .execute()
    )

    return policy


def set_policy(credentials, project_id, policy):
    """Sets IAM policy for a project."""

    minimum_policy_version = 3
    if policy["version"] < minimum_policy_version:
        # The policy may be version 1 as this is the default in GCP
        # it needs to be at least version 3 to support conditional bindings
        LOG.debug("Overriding GCP IAM Policy version, was %s is now %s", policy["version"], minimum_policy_version)
        policy["version"] = minimum_policy_version

    service = googleapiclient.discovery.build(
        "cloudresourcemanager", "v1", credentials=credentials,
        cache_discovery=False
    )

    policy = (
        service.projects()
        .setIamPolicy(resource=project_id, body={"policy": policy})
        .execute()
    )

    LOG.info("Updated IAM Policy for project %s", project_id)

    return policy


def modify_policy_remove_member(policy, roles, member):
    """Removes a member from a role binding if the role is in the given roles"""

    # Policy has no bindings to remove
    if "bindings" not in policy:
        return policy

    for binding in policy["bindings"]:
        if binding["role"] not in roles:
            LOG.debug("Ignoring binding, role %s not supported", binding["role"])

        if "members" not in binding:
            LOG.debug("Ignoring binding, role %s has no members", binding["role"])

        # If member exists in the binding, remove the member
        if member in binding["members"]:
            condition_name = None if "condition" not in binding else binding["condition"]["title"]
            LOG.debug("Removed %s from role %s with condition '%s'", member, binding["role"], condition_name)
            binding["members"].remove(member)

    policy["bindings"] = _remove_bindings_without_members(policy["bindings"], roles)


def modify_policy_add_binding(policy, role, member, condition):
    """Adds a new role binding to a policy."""

    binding = {
        "role": role,
        "members": [member],
        "condition": condition
    }
    policy["bindings"].append(binding)

    condition_name = None if condition is None or "title" not in condition else condition["title"]
    LOG.info("Added role binding for %s from role %s with condition '%s'", member, role, condition_name)

    return policy


def _remove_bindings_without_members(bindings: list, roles: list):
    """Removes any bindings that have no members if the role is in the given roles"""
    new_bindings = []
    for binding in bindings:
        if "members" in binding and binding["members"] or binding["role"] not in roles:
            # this is a supported role, and has at least one member
            # or it is not a supported role, and should not be modified by foremast
            new_bindings.append(binding)
        elif binding["role"] in roles:
            # this is a supported role, but has no members
            LOG.debug("Removed empty role binding for role %s", binding["role"])

    return new_bindings
