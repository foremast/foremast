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
"""GCP IAM Secrets Manager management"""

import logging

from . import modify_policy_add_binding
from ..utils.gcp_environment import GcpEnvironment

LOG = logging.getLogger(__name__)


def modify_policy_grant_secrets(env: GcpEnvironment, policy: dict, secrets: list, member: str):

    # ToDo: Use Condition generator?
    condition = {
        "expression": "",
        "title": "Foremast: Managed Secrets Access"
    }

    secret_names = []
    for secret in secrets:
        secret_name = "projects/{}/secrets/{}/".format(env.secret_manager_project, secret)
        secret_names.append(secret_name)
        secret_condition = 'resource.name.startsWith("{0}")'.format(secret_name)
        # Append to existing conditions
        if condition["expression"]:
            condition["expression"] = condition["expression"] + " || " + secret_condition
        else:
            condition["expression"] = secret_condition

    role = "roles/secretmanager.secretAccessor"
    LOG.info("Granted role %s on secrets %s", role, secret_names)
    modify_policy_add_binding(policy, role, member, condition)
