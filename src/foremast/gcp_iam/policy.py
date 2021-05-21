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


def modify_policy_remove_member(policy, member):
    """Removes a member from a role binding if the role is in the given roles.
    Returns true if that member was found and removed, false is the member was
    not found."""
    was_updated = False

    # Policy has no bindings to remove
    if "bindings" not in policy:
        return was_updated

    for binding in policy["bindings"]:
        # If member exists in the binding, remove the member
        if "members" in binding and member in binding["members"]:
            LOG.debug("Removed %s from role %s", member, binding["role"])
            binding["members"].remove(member)
            was_updated = True

    return was_updated


def modify_policy_add_binding(policy, role, member):
    """Adds a new role binding to a policy."""

    binding = {
        "role": role,
        "members": [member]
    }
    policy["bindings"].append(binding)

    LOG.info("Added role binding for %s from role %s", member, role)

    return policy
