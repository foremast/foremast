from googleapiclient.errors import HttpError

from ..utils.gcp_environment import GcpEnvironment
from . import create_service_account, get_policy, set_policy, modify_policy_remove_member, modify_policy_add_binding
from tryagain import retries

import logging

LOG = logging.getLogger(__name__)


def create_iam_resources(env: GcpEnvironment, app_name: str, services: dict = None):
    credentials = env.get_credentials()
    # Ensure service account is created
    service_account = create_service_account(credentials=credentials,
                                             project_id=env.service_account_project,
                                             name=app_name)
    member = "serviceAccount:" + service_account["email"]

    # Get the gcp_roles requested in pipeline.json with the full project id as the key
    gcp_roles_by_project = _get_gcp_roles_by_project(services['gcp_roles'], env) if "gcp_roles" in services else dict()

    # For each project in this GCP environment, get the policy
    # remove any references to this svc account, then re-add based on pipeline.json
    # If changes were made locally, update the policy in GCP
    for project in env.get_all_projects():
        _update_policy_for_project(project['projectId'], gcp_roles_by_project, member, credentials)

    LOG.info("Finished configuring GCP IAM")


@retries(max_attempts=5, wait=lambda n: 2 ** n, exceptions=HttpError)
def _update_policy_for_project(project_id, roles_by_project, member, credentials):
    # Policies in GCP are shared between users/service accounts
    # Attempt to update this project policy, if GCP returns a
    # a 409 conflict we must re-retrieve the policy, re-update it
    # and attempt to save again to save it again
    try:
        LOG.info("Preparing to update IAM policy for project %s", project_id)
        policy = get_policy(credentials, project_id)
        # Remove any references to this svc account from policy
        policy_was_updated = modify_policy_remove_member(policy, member)

        # Update policy
        if project_id in roles_by_project:
            policy_was_updated = True
            # Add all roles in pipeline.json for this project
            for role in roles_by_project[project_id]['roles']:
                modify_policy_add_binding(policy=policy, role=role, member=member)

        # if the policy was edited, send to Google APIs
        if policy_was_updated:
            LOG.info("IAM Policy for project {} will be updated because it was modified locally"
                     .format(project_id))
            set_policy(credentials=credentials, project_id=project_id, policy=policy)
        else:
            LOG.info("IAM Policy for project {} will not be updated because it was not modified locally"
                     .format(project_id))
    except HttpError as e:
        # Conflict while updating
        if 'status' in e.resp and e.resp['status'] == '409':
            LOG.warning("GCP returned 409 conflict, this policy was recently updated elsewhere.  "
                        "Will retry up to 5 times per project.")
        raise e


def _get_gcp_roles_by_project(gcp_roles, env: GcpEnvironment):
    """Gets the full project name for the given services.gcp_roles block

    Returns a dictionary where the key is the full project name, and the value
    is the corresponding entry from services.gcp_roles"""

    roles_by_project = dict()

    for role_definition in gcp_roles:
        project = env.get_project(project_prefix=role_definition['project_prefix'])
        roles_by_project[project['projectId']] = role_definition

    return roles_by_project
