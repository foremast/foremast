from ..utils.gcp_environment import GcpEnvironment
from . import create_service_account, get_policy, set_policy, modify_policy_remove_member, modify_policy_grant_secrets

import logging

LOG = logging.getLogger(__name__)


def create_iam_resources(env: GcpEnvironment, app_name: str, services: dict = None):
    credentials = env.get_credentials()
    # Ensure service account is created
    service_account = create_service_account(credentials=credentials,
                                                     project_id=env.service_account_project,
                                                     name=app_name)
    member = "serviceAccount:" + service_account["email"]

    # Get the current project policy, and remove any managed roles for the svc account
    policy = get_policy(credentials, env.secret_manager_project)
    modify_policy_remove_member(policy, ["roles/secretmanager.secretAccessor"], member)

    # Add roles managed by foremast
    if services:
        # In GCP it is secretmanager (not plural), but support both so people don't hate us
        if "secretmanager" in services or "secretsmanager" in services:
            if "secretmanager" in services:
                secrets = services["secretmanager"]
            else:
                secrets = services["secretsmanager"]

            modify_policy_grant_secrets(env, policy, secrets, member)

    # save policy in GCP
    set_policy(credentials, env.secret_manager_project, policy)

    LOG.info("Finished configuring GCP IAM")