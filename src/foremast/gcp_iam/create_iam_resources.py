from ..utils.gcp_environment import GcpEnvironment
from . import create_service_account, get_policy, set_policy, modify_policy_remove_member, modify_policy_add_binding

import logging

LOG = logging.getLogger(__name__)

GCP_IAM_ROLE_SECRETS = "roles/secretmanager.secretAccessor"
GCP_IAM_ROLE_DATASTORE = "roles/datastore.user"
GCP_IAM_ROLE_PUBSUB_EDITOR = "roles/pubsub.editor"
GCP_IAM_ROLE_PUBSUB_VIEWER = "roles/pubsub.viewer"
GCP_IAM_ROLE_PUBSUB_PUBLISHER = "roles/pubsub.publisher"
GCP_IAM_ROLE_PUBSUB_SUBSCRIBER = "roles/pubsub.subscriber"
GCP_IAM_ROLES = [GCP_IAM_ROLE_SECRETS, GCP_IAM_ROLE_DATASTORE,
                 GCP_IAM_ROLE_PUBSUB_EDITOR, GCP_IAM_ROLE_PUBSUB_PUBLISHER, GCP_IAM_ROLE_PUBSUB_SUBSCRIBER,
                 GCP_IAM_ROLE_PUBSUB_VIEWER]


def create_iam_resources(env: GcpEnvironment, app_name: str, services: dict = None):
    credentials = env.get_credentials()
    # Ensure service account is created
    service_account = create_service_account(credentials=credentials,
                                             project_id=env.service_account_project,
                                             name=app_name)
    member = "serviceAccount:" + service_account["email"]

    # Organize the users services block by project to reduce API calls
    service_by_project = _get_services_by_project(services, env)

    # For each project in this GCP environment, get the policy
    # remove any references to this svc account, then re-add based on pipeline.json
    # and save (if changes were made)
    for project in env.get_all_projects():
        project_id = project["projectId"]
        policy = get_policy(credentials, project_id)
        # Remove any references to this svc account from policy (ignoring roles foremast does not support)
        policy_was_updated = modify_policy_remove_member(policy, GCP_IAM_ROLES, member)

        # If pipeline.json has resources referencing this project
        if project_id in service_by_project:
            policy_was_updated = True
            project_services = service_by_project[project_id]
            # SecretsManager:
            # In GCP it is secretmanager (not plural), but support both so people don't hate us
            if "secretmanager" in project_services or "secretsmanager" in project_services:
                modify_policy_add_binding(policy, GCP_IAM_ROLE_SECRETS, member, condition=None)
            # Datastore
            if "datastore" in project_services:
                modify_policy_add_binding(policy, GCP_IAM_ROLE_DATASTORE, member, condition=None)
            # Pub/Sub
            if "pubsub" in project_services:
                for pub_sub in project_services["pubsub"]:
                    if "roles" not in pub_sub:
                        raise KeyError("Roles must be defined when requested PubSub IAM access")
                    if "editor" in pub_sub['roles']:
                        modify_policy_add_binding(policy, GCP_IAM_ROLE_PUBSUB_EDITOR, member, condition=None)
                    if "viewer" in pub_sub['roles']:
                        modify_policy_add_binding(policy, GCP_IAM_ROLE_PUBSUB_VIEWER, member, condition=None)
                    if "subscriber" in pub_sub['roles']:
                        modify_policy_add_binding(policy, GCP_IAM_ROLE_PUBSUB_SUBSCRIBER, member, condition=None)
                    if "publisher" in pub_sub['roles']:
                        modify_policy_add_binding(policy, GCP_IAM_ROLE_PUBSUB_PUBLISHER, member, condition=None)

        # if the policy was edited, send to Google APIs
        if policy_was_updated:
            LOG.info("IAM Policy for project {} will be updated because it was modified locally".format(project_id))
            set_policy(credentials, project_id, policy)
        else:
            LOG.info("IAM Policy for project {} will not be updated because it was not modified locally"
                     .format(project_id))

    LOG.info("Finished configuring GCP IAM")


def _get_services_by_project(services: dict, env: GcpEnvironment):
    """Re-organizes a services block by project.  The project id
     as returned from the Google Resource Manager API is used.

    Example structure:

    project1-id:
      secretsmanager:
        - resource
        - resource2
    project2-id:
      secretsmanager:
        - resource3
        - resource4
    """

    services_by_project = dict()
    # Loop all services declared (e.g. secretsmanager)
    for service_type in services:
        for resource in services[service_type]:
            if 'project' not in resource or not resource['project']:
                raise KeyError("Project key missing for an item in service type {}".format(service_type))
            project_prefix = resource['project']
            project = env.get_project(project_prefix)
            project_id = project['projectId']
            # If this is the first time the project is referenced, create the key
            if project_id not in services_by_project:
                services_by_project[project_id] = dict()
            # If this project does not have this service yet, add it
            if service_type not in services_by_project[project_id]:
                services_by_project[project_id][service_type] = []
            # Finally add this resource
            services_by_project[project_id][service_type].append(resource)

    return services_by_project


