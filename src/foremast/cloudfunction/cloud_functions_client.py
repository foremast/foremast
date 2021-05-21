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
"""Client for deploying GCP Cloud Functions"""

import logging
import requests
from googleapiclient.errors import HttpError
from googleapiclient import discovery
from ..exceptions import CloudFunctionDeployError, CloudFunctionOperationFailedError, \
    CloudFunctionOperationIncompleteError
from tryagain import retries
from ..utils.gcp_environment import GcpEnvironment

LOG = logging.getLogger(__name__)


class CloudFunctionsClient:

    def __init__(self, app_name, env: GcpEnvironment, configs, use_service_account=True):
        """Creates a new GcpEnvironment object
        Args:
            app_name (str): Full name off app (e.g. coolappneatproject)
            env (GcpEnvironment): GCP Environment to target
            configs (dict): Pipeline configs
            use_service_account (bool): When true a service account {app_name}@{project}.iam.gserviceaccount.com is
                assigned to the function.  It is assumed this service account exists already.  Defaults to True.
        """
        credentials = env.get_credentials()
        api_builder = discovery.build('cloudfunctions', 'v1', credentials=credentials)
        self._env = env
        self._functions_client = api_builder.projects().locations().functions()
        self._operations_client = api_builder.operations()
        self._pipeline_config = configs['pipeline']  # pipeline.json options
        self._cf_config = self._pipeline_config['cloudfunction']  # pipeline.json, cloudfunction block
        self._env_config = configs[env.name]  # application-master-{env}.json options
        self._name = app_name
        self._project_id = None
        self._regions = list()
        self._use_service_account = use_service_account
        self._service_account_email = None

    def prepare_client(self):
        # Load project name, this may require API calls to GCP
        # and should not be in __init__
        try:
            project_wildcard = self._cf_config["project_name"]
            self._project_id = self._env.get_project(project_wildcard)['projectId']
        except KeyError:
            LOG.error("Missing required field: cloudfunction.project_name in pipeline.json")
            raise

        try:
            self._regions = self._env_config['regions']
            if not self._regions:
                raise ValueError("At least one region must be defined")
        except (KeyError, ValueError):
            LOG.error("Cloud Function pipelines require at least one region in pipeline.json")
            raise

        if self._use_service_account:
            self._service_account_email = "{}@{}.iam.gserviceaccount.com".format(self._name, self._project_id)
            LOG.info("Using dedicated service account '%s'", self._service_account_email)

    def deploy_function(self, file_path, region):
        """Creates (or updates) and uploads a function's code in one step

        Args:
            file_path: str, required
                Local file path to the function's zip file
            region: str, required
                The region to deploy to

        Returns:
            None

        Raises:
            CloudFunctionOperationIncompleteError: Timeout waiting for the operation to complete
            CloudFunctionOperationFailedError: Operation completed with error
            HttpError: Error communicating with the GCP APIs
        """
        if region not in self._regions:
            raise CloudFunctionDeployError("Region '{}' is not in cloud function's configuration.  Options are: {}"
                                           .format(region, self._regions))

        upload_url = self._get_upload_url(region)
        self._upload_zip(upload_url, file_path)
        exists = self._check_function_exists(region)
        # Deploy function, then update it's IAM Policy for access
        if exists:
            self._update_function(region, upload_url)
        else:
            self._create_function(region, upload_url)
        self._update_function_iam_policy(region)

    def _get_upload_url(self, location_id):
        """Gets a Signed URL that the function's zip file can be uploaded to

        Args:
            location_id: str, required
                Location Id (region) the function will be uploaded to.  (e.g. us-east1)
        """
        parent = "projects/{}/locations/{}".format(self._project_id, location_id)
        result = self._functions_client.generateUploadUrl(parent=parent, body={}).execute()
        return result["uploadUrl"]

    def _upload_zip(self, upload_url, file_path):
        """Uploads a function's local zip file to the destination url given

        Args:
            upload_url: str, required
                The signed URL generated using get_upload_url()
            file_path: str, required
                The local path to the zip file to be uploaded
        """

        with open(file_path, 'rb') as file:
            # Note: The upload_url will be a signed URL generated for us
            # Do not set BEARER auth header
            headers = {
                'content-type': 'application/zip',
                'x-goog-content-length-range': '0,104857600'
            }
            result = requests.put(upload_url, data=file, headers=headers)
            result.raise_for_status()
            LOG.info("Successfully uploaded cloud function code")

    def _create_function(self, location_id, upload_url):
        """Creates a new Cloud Function

            Args:
                location_id (str): Location Id (Region)

            Returns:
                None

            Raises:
                CloudFunctionOperationIncompleteError: Timeout waiting for the operation to complete
                CloudFunctionOperationFailedError: Operation completed with error
                HttpError: Error communicating with the GCP APIs
        """
        parent = "projects/{}/locations/{}".format(self._project_id, location_id)
        request_body = self._generate_function_request_body(location_id, upload_url)

        LOG.info("Creating cloud function '%s' in region '%s' and project '%s'",
                 self._name, location_id, self._project_id)
        response = self._functions_client.create(location=parent, body=request_body).execute()
        # If operation times out or fails an exception will be raised to stop the pipeline
        self._wait_for_operation(response['name'])
        LOG.info("Successfully created cloud function '%s' in region '%s' and project '%s'",
                 self._name, location_id, self._project_id)

    def _update_function(self, location_id, upload_url):
        """Updates an existing Cloud Function

            Args:
                location_id (str): Location Id (Region)

            Returns:
                None

            Raises:
                CloudFunctionOperationIncompleteError: Timeout waiting for the operation to complete
                CloudFunctionOperationFailedError: Operation completed with error
                HttpError: Error communicating with the GCP APIs
        """
        full_name = self._generate_function_path(location_id)
        request_body = self._generate_function_request_body(location_id, upload_url)
        LOG.info("Updating cloud function '%s' in region '%s' and project '%s'",
                 self._name, location_id, self._project_id)
        response = self._functions_client.patch(name=full_name, body=request_body).execute()
        # If operation times out or fails an exception will be raised to stop the pipeline
        self._wait_for_operation(response['name'])
        LOG.info("Successfully updated cloud function '%s' in region '%s' and project '%s'",
                 self._name, location_id, self._project_id)

    def _update_function_iam_policy(self, region: str):
        """Updates a function's individual IAM Policy which is used to control access to the cloud function
        For example, limiting access to a certain service account or allowing unauthenticated access

            Args:
                region (str): Region the function is deployed to (e.g. us-east1)

            Returns:
                None
        """
        resource_name = self._generate_function_path(region)
        bindings = []
        # If they use the helper allow_unauthenticated add the binding for them
        # Equivilent of gcloud functions deploy ... --allow-unauthenticated
        allow_unauthenticated = self._env_config['app'].get("cloudfunction_allow_unauthenticated", False)
        custom_bindings = self._env_config['app'].get("cloudfunction_iam_bindings", [])
        if allow_unauthenticated:
            bindings.append(CloudFunctionsClient._get_allow_unauthenticated_binding())
        if custom_bindings:
            bindings.extend(custom_bindings)
        LOG.info("Updating Cloud Function IAM Policy for '%s' in region '%s' and project '%s': Bindings '%s'",
                 self._name, region, self._project_id, bindings)
        body_payload = {
            "policy": {
                "bindings": bindings
            }
        }
        self._functions_client.setIamPolicy(resource=resource_name, body=body_payload).execute()

    def _check_function_exists(self, location_id):
        """Checks a GCP Cloud Function exists

            Args:
                location_id (str): Region to check for the function in

            Returns:
                True: When function exists
                False: When function does not exist
        """
        full_name = self._generate_function_path(location_id)
        try:
            self._functions_client.get(name=full_name).execute()
            return True
        except HttpError as e:
            # 404 is expected if the function does not exist
            # any other HttpError would should be re-raised
            if 'status' in e.resp and e.resp['status'] == '404':
                return False
            raise e

    # Retry with back off, wait time is attempt_count * 2 (1 second, 2 seconds, 4 seconds, etc.)
    @retries(max_attempts=10, wait=lambda n: 2 ** n, exceptions=CloudFunctionOperationIncompleteError)
    def _wait_for_operation(self, operation_name):
        """Waits for the given operation to complete with an exponential back off.  The back off is
        the number of attempts multiplied by two (in seconds).  Maximum 10 attempts total, for a total of
        110 seconds waiting before timing out.

            Args:
                operation_name (str): Name of the operation in form 'operation/{id}'

            Raises:
                CloudFunctionOperationIncompleteError: Timeout waiting for the operation to complete
                CloudFunctionOperationFailedError: Operation completed with error
            """
        LOG.info("Waiting for operation to complete.  Will poll GCP periodically.")
        response = self._operations_client.get(name=operation_name).execute()
        # If done is false, or no 'done' key is present, the operation is still running
        # If done, and error are set, it completed with a failure.  Typically this means there is
        # an issue with the function's code and the user should be made aware
        done = response.get('done', False)
        error = response.get('error', None)
        if done and error:
            raise CloudFunctionOperationFailedError(error, "Cloud Function deployment failed: {}".format(error))
        elif done:
            return
        else:
            # Raise error to trigger back off
            raise CloudFunctionOperationIncompleteError()

    def _generate_function_path(self, location_id):
        return "projects/{}/locations/{}/functions/{}".format(self._project_id, location_id, self._name)

    def _generate_function_request_body(self, location_id, upload_url):
        """Generates the request body for create and update/patch cloud function API calls to GCP using
        defaults and pipeline configuration files for the current repo.

           Args:
               location_id (str): The region being deployed to
               upload_url (str): The URL of the already uploaded/zipped source code

           Returns:
               dict: Response body for GCP create/patch function API calls
       """
        app_config = self._env_config['app']
        vpc_connector_block = app_config.get("cloudfunction_vpc", {})

        request_body = {
            # Automated options
            "name": self._generate_function_path(location_id),
            "serviceAccountEmail": self._service_account_email,
            "sourceUploadUrl": upload_url,
            # General pipeline options
            "entryPoint": self._cf_config['entry_point'],
            "runtime": self._cf_config['runtime'],
            "labels": {},
            # Env specific options
            "timeout": app_config.get("cloudfunction_timeout"),
            "availableMemoryMb": app_config.get("cloudfunction_memory_mb"),
            "environmentVariables": app_config.get("cloudfunction_environment"),
            "maxInstances": app_config.get("cloudfunction_max_instances"),
            # Get the connector name for this region
            "vpcConnector":  vpc_connector_block.get("connector", {}).get(location_id),
            "vpcConnectorEgressSettings": vpc_connector_block.get("egress_type"),
            "ingressSettings": app_config.get("cloudfunction_ingress_type")
        }

        # GCP only supports either an HTTP trigger or an event trigger, both can not be used
        # HTTP Trigger is the default and can work with no configuration
        # if they did not give an event trigger, assume HTTP
        event_trigger = app_config.get("cloudfunction_event_trigger")
        if event_trigger:
            if "failure_policy" in event_trigger and event_trigger["failure_policy"].get("retry"):
                # GCP API specifies this as an object, but it is more of a bool depending on if the obj is set or not
                retry = {}
            else:
                retry = None
            request_body["eventTrigger"] = {
                "eventType": event_trigger["event_type"],
                "resource": self._get_full_resource_path(event_trigger["resource"]),
                "service": event_trigger.get("service"),
                "failurePolicy": {
                    "retry": retry
                }
            }
        else:
            request_body["httpsTrigger"] = {}

        return request_body

    def _get_full_resource_path(self, partial_path):
        """Translates a partial resource path `topics/my_topic` or `/topics/my_topic`
        to the full path including project, like `/projects/my-project/topics/my_topic`.
        Most GCP APIs expect the full path.  The deployment target project is used, as GCP
        Functions can only be triggered by a resource in the same project.

        Args:
            partial_path (str): The partial resource path

        GCP Docs: https://cloud.google.com/functions/docs/reference/rest/v1/projects.locations.functions#EventTrigger"""

        if partial_path.startswith("projects"):
            raise CloudFunctionDeployError("Path '{}' contains a hardcoded project identifier. ".format(partial_path) +
                                           "Foremast adds this automatically based on the target deployment project. " +
                                           "Path should start at the event type (e.g. databases, bucket, etc).")

        return "projects/{}/{}".format(self._project_id, partial_path.lstrip('/'))

    @staticmethod
    def _get_allow_unauthenticated_binding():
        """
        Gets an IAM Policy binding that will allow anonymous access to a Cloud Function
        See: https://cloud.google.com/functions/docs/securing/managing-access-iam
        Is equivilent of gcloud function deploy ... --allow-unauthenticated

        Returns:
            Dict, Single IAM Policy binding object: https://cloud.google.com/functions/docs/reference/rest/v1/Policy
        """
        return {
            "members": [
                "allUsers"
            ],
            "role": "roles/cloudfunctions.invoker"
        }
