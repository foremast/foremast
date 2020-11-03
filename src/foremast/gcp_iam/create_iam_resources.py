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
"""GCP IAM Resource management"""

from googleapiclient.errors import HttpError

from ..utils import get_template_object
from ..exceptions import ForemastError
from ..utils.gcp_environment import GcpEnvironment
from . import get_policy, set_policy, modify_policy_remove_member, modify_policy_add_binding
from tryagain import retries
import googleapiclient.discovery
import json
import logging

LOG = logging.getLogger(__name__)


class GcpIamResourceClient:

    def __init__(self, env, app_name, group_name, repo_name, configs):
        self._env = env
        self._credentials = env.get_credentials()
        self._configs = configs
        self._pipeline_type = configs["pipeline"]["type"]
        self._app_name = app_name
        self._group_name = group_name
        self._repo_name = repo_name
        self._services = configs["pipeline"].get('services', dict())

    def create_iam_resources(self):
        """Creates IAM resources including service accounts and IAM role bindings

        Returns:
            Str: the email of the svc account that was created/updated with IAM bindings"""

        # Ensure service account is created
        service_account = self._create_service_account()
        service_account_name = service_account["name"]
        service_account_email = service_account["email"]
        member = "serviceAccount:" + service_account_email
        # Update individual svc account's IAM Policy
        # This is optional and used to grant access TO this svc account, NOT to grant this svc account
        # access to other resources
        self._update_policy_for_service_account(service_account_name)

        # Get the gcp_roles requested in pipeline.json with the full project id as the key
        gcp_roles_by_project = GcpIamResourceClient._get_gcp_roles_by_project(self._services.get('gcp_roles', list()),
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
                dict, Service account with the following keys:
                    name
                    email
                    projectId
                    uniqueId
                    displayName
                    description
            """
        svc_account_name = "projects/{project}/serviceAccounts/{name}@{project}.iam.gserviceaccount.com"\
                           .format(project=self._get_service_account_project(), name=self._app_name)
        service = googleapiclient.discovery.build(
            'iam', 'v1', credentials=self._credentials, cache_discovery=False)
        try:
            response = service.projects().serviceAccounts().get(name=svc_account_name).execute()
            return response
        except HttpError as e:
            if 'status' in e.resp and e.resp['status'] == '404':
                LOG.warning("Did not find existing service account %s", svc_account_name)
                return None
            raise e

    @retries(max_attempts=5, wait=lambda n: 2 ** n, exceptions=HttpError)
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
        try:
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
        except HttpError as e:
            # Conflict while updating
            if 'status' in e.resp and e.resp['status'] == '409':
                LOG.warning("GCP returned 409 conflict, this service account may already exist. "
                            "Will retry up to 5 times per project.")
            raise e

    def _get_service_account_project(self):
        """Gets the projectId that should be used when creating the svc account"""
        if self._pipeline_type == "cloudfunction":
            # Override to the same project the function will be deployed to
            cloud_function_project = self._env.get_project(self._configs["pipeline"]["cloudfunction"]["project_name"])
            return cloud_function_project["projectId"]

        # Default is the service account project defined for this env in Foremast config
        return self._env.service_account_project

    @retries(max_attempts=5, wait=lambda n: 2 ** n, exceptions=HttpError)
    def _update_policy_for_service_account(self, resource_name):
        """Updates the IAM policy attached to the given service account
        Args:
            resource_name (str): The service account's full resource name (e.g. projects/../serviceAccounts/..)
        Returns:
            None
        """
        template = get_template_object('infrastructure/iam/gcp-service-account.json.j2')
        rendered_template = template.render(**self._get_jinja_args())
        # If the rendered template is just whitespace, skip the step
        if not rendered_template or rendered_template.isspace():
            LOG.debug("Skipping IAM Policy update for service account '%s' (this is not the same as updating IAM "
                      "bindings on projects)", resource_name)
            return
        # Get/update svc account's IAM Policy
        try:
            service_account_api = googleapiclient.discovery.build(
                'iam', 'v1', credentials=self._credentials, cache_discovery=False).projects().serviceAccounts()
            iam_policy = service_account_api.getIamPolicy(resource=resource_name).execute()
            iam_policy["bindings"] = json.loads(rendered_template)
            body_payload = {
                "policy": iam_policy
            }
            LOG.info("Updating svc account '%s' IAM policy bindings: '%s'", resource_name, rendered_template)
            service_account_api.setIamPolicy(resource=resource_name, body=body_payload).execute()
        except HttpError as e:
            # Conflict while updating
            if 'status' in e.resp and e.resp['status'] == '409':
                LOG.warning("GCP returned 409 conflict, this service account policy was recently updated elsewhere.  "
                            "Will retry up to 5 times per service account policy.")
            raise e

    def _get_jinja_args(self):
        return {
            'app': self._app_name,
            'group': self._group_name,
            'repo': self._repo_name,
            'pipeline_type': self._pipeline_type,
            'env': self._env.name
        }

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
        foremast_groups = project['labels']['foremast_groups'].split('__')  # split on two underscores
        LOG.debug("Project '%s' only supports foremast deployments from groups: '%s'", project['projectId'],
                  foremast_groups)
        for permitted_group in foremast_groups:
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
        Returns:
            list: List of service accounts, empty list if none exist
        """
        service = googleapiclient.discovery.build(
            'iam', 'v1', credentials=credentials, cache_discovery=False)

        service_accounts = service.projects().serviceAccounts().list(
            name='projects/' + project_id).execute()

        return service_accounts.get('accounts', list())
