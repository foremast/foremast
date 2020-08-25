from googleapiclient.errors import HttpError

from ..exceptions import ForemastError
from ..utils.gcp_environment import GcpEnvironment
from . import get_policy, set_policy, modify_policy_remove_member, modify_policy_add_binding
from tryagain import retries
import googleapiclient.discovery

import logging

LOG = logging.getLogger(__name__)


class GcpIamResourceClient:

    def __init__(self, env, app_name, group_name, configs):
        self._env = env
        self._credentials = env.get_credentials()
        self._configs = configs
        self._pipeline_type = configs["pipeline"]["type"]
        self._app_name = app_name
        self._group_name = group_name
        self._services = configs["pipeline"].get('services', dict())

    def create_iam_resources(self):
        """Creates IAM resources including service accounts and IAM role bindings

        Returns:
            Str: the email of the svc account that was created/updated with IAM bindings"""

        # Ensure service account is created
        service_account = self._create_service_account()
        service_account_email = service_account["email"]
        member = "serviceAccount:" + service_account_email

        # Update services block with any minimum default roles needed
        self._apply_role_defaults()

        # Get the gcp_roles requested in pipeline.json with the full project id as the key
        gcp_roles_by_project = GcpIamResourceClient._get_gcp_roles_by_project(self._services['gcp_roles'],
                                                                              self._env, self._group_name)

        # For each project in this GCP environment, get the policy
        # remove any references to this svc account, then re-add based on pipeline.json
        # If changes were made locally, update the policy in GCP
        for project in self._env.get_all_projects():
            GcpIamResourceClient._update_policy_for_project(project['projectId'], gcp_roles_by_project, member,
                                                            self._credentials)

        LOG.info("Finished configuring GCP IAM")
        return service_account_email

    def _get_service_account(self):
        """Gets a service account
            Returns:
                dict, Created service account with the following keys:
                    name
                    email
                    projectId
                    uniqueId
                    displayName
                    description
            """
        service_accounts = GcpIamResourceClient.list_service_accounts(credentials=self._credentials,
                                                                      project_id=self._get_service_account_project())
        
        # Check if the SA already exists
        for account in service_accounts['accounts']:
            if self._app_name == account['displayName']:
                return account
        return None

    def _create_service_account(self):
        """Creates a service account.
        Returns:
            dict, Created service account with the following keys:
                name
                email
                projectId
                uniqueId
                displayName
                description
        """

        existing_account = self._get_service_account()
        if existing_account:
            LOG.info("GCP service account %s already exists", existing_account['email'])
            return existing_account

        LOG.info("GCP service account for pipeline does not already exist")
        svc_project = self._get_service_account_project()

        service = googleapiclient.discovery.build(
            'iam', 'v1', credentials=self._credentials, cache_discovery=False)

        app_svc_account = service.projects().serviceAccounts().create(
            name='projects/' + svc_project,
            body={
                'accountId': self._app_name,
                'serviceAccount': {
                    'displayName': self._app_name,
                    'description': 'Managed by Foremast'
                }
            }).execute()

        LOG.info("Created GCP service account with email %s", app_svc_account['email'])
        return app_svc_account

    def _get_service_account_project(self):
        """Gets the projectId that should be used when creating the svc account"""
        if self._pipeline_type == "cloudfunction":
            # Override to the same project the function will be deployed to
            cloud_function_project = self._env.get_project(self._configs["pipeline"]["cloudfunction"]["project_name"])
            return cloud_function_project["projectId"]

        # Default is the service account project defined for this env in Foremast config
        return self._env.service_account_project

    def _apply_role_defaults(self):
        """Appends any default/minimum roles to services block that may be required to deploy the given pipeline type"""

        if "gcp_roles" not in self._services:
            self._services["gcp_roles"] = list()

        if self._pipeline_type == "cloudfunction":
            LOG.info("Adding additional roles to cloud function service account")
            self._services["gcp_roles"].append({
                "project_name": self._configs["pipeline"]["cloudfunction"]["project_name"],
                "roles": [
                    "roles/iam.serviceAccountUser",
                    "roles/cloudfunctions.admin",
                    "roles/cloudfunctions.serviceAgent"
                ]
            })

    @staticmethod
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

    @staticmethod
    def _get_gcp_roles_by_project(gcp_roles: list, env: GcpEnvironment, group_name: str):
        """Gets the full project name for the given services.gcp_roles block

        Returns a dictionary where the key is the full project name, and the value
        is the corresponding entry from services.gcp_roles

        Raises ForemastError if a requested role is not permitted on the given project"""
        roles_by_project = dict()

        for role_definition in gcp_roles:
            project = env.get_project(project_name=role_definition['project_name'])
            # If they are not permitted to request roles on this project, stop Foremast now:
            if not GcpIamResourceClient._check_group_permitted_project(project, group_name):
                raise ForemastError("Group '{}' is not permitted to request roles in "
                                    "project '{}'".format(group_name, project['projectId']))

            # Cleared to request roles in this project
            # Check if the project key already exists, if so merge the roles.  This can happen
            # when Foremast adds a minimum set of roles, and the user also requested their own roles
            project_id = project['projectId']
            if project_id in roles_by_project:
                roles_by_project[project_id]["roles"].extend(role_definition["roles"])
            else:
                roles_by_project[project_id] = role_definition

        return roles_by_project

    @staticmethod
    def _check_group_permitted_project(project, group_name):
        """Returns true if a group is permitted to access this project based on
        the projects FOREMAST_GROUPS=team1,team2 label.  If no label is present
        all groups are permitted."""

        if 'foremast_groups' not in project['labels'] or not project['labels']['foremast_groups'].strip():
            LOG.debug("Project '%s' permits access from all groups", project['projectId'])
            return True

        # foremast_groups defined and not empty
        foremast_groups_csv = project['labels']['foremast_groups']
        LOG.debug("Project '%s' only supports foremast deployments from groups: '%s'", project['projectId'],
                  foremast_groups_csv)
        for permitted_group in foremast_groups_csv.split(','):
            if group_name == permitted_group.strip():
                return True

        # Default to denied
        return False

    @staticmethod
    def list_service_accounts(credentials, project_id=None):
        """Lists all service accounts for the given project.
        Args:
            credentials: GCP API Credentials for a service account
            project_id (str): The project to target
        """
        service = googleapiclient.discovery.build(
            'iam', 'v1', credentials=credentials, cache_discovery=False)

        service_accounts = service.projects().serviceAccounts().list(
            name='projects/' + project_id).execute()

        return service_accounts
