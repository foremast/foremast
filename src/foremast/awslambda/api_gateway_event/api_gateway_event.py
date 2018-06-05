#   Foremast - Pipeline Tooling
#
#   Copyright 2018 Gogo, LLC
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
"""Handle API Gateway events"""

import logging

import boto3
import botocore
from tryagain import retries

from foremast.utils import (add_lambda_permissions, get_details, get_env_credential, get_lambda_alias_arn,
                            get_lambda_arn, get_properties)

LOG = logging.getLogger(__name__)


class APIGateway:
    """Class to handle API Gateway and Lambda integration.

    Args:
        app (str): Application Name
        env (str): Environment/account for deployments
        region (str): AWS Region
        rules (dict): Trigger settings
        prop_path (str): Path to the raw.properties.json
    """

    def __init__(self, app='', env='', region='', rules={}, prop_path=''):
        self.log = logging.getLogger(__name__)
        self.generated = get_details(app=app, env=env)
        self.trigger_settings = rules
        self.app_name = self.generated.app_name()
        self.env = env
        self.account_id = get_env_credential(env=self.env)['accountId']
        self.region = region
        self.properties = get_properties(properties_file=prop_path, env=self.env, region=self.region)

        session = boto3.Session(profile_name=env, region_name=region)
        self.client = session.client('apigateway')
        self.lambda_client = session.client('lambda')
        self.api_version = self.lambda_client.meta.service_model.api_version

        self.api_id = self.find_api_id()
        self.resource_id, self.parent_id = self.find_resource_ids()

    def find_api_id(self):
        """Given API name, find API ID."""
        allapis = self.client.get_rest_apis()
        api_name = self.trigger_settings['api_name']
        api_id = None
        for api in allapis['items']:
            if api['name'] == api_name:
                api_id = api['id']
                self.log.info("Found API for: %s", api_name)
                break
        else:
            api_id = self.create_api()

        return api_id

    def find_resource_ids(self):
        """Given a resource path and API Id, find resource Id."""
        all_resources = self.client.get_resources(restApiId=self.api_id)
        parent_id = None
        resource_id = None
        for resource in all_resources['items']:
            if resource['path'] == "/":
                parent_id = resource['id']
            if resource['path'] == self.trigger_settings['resource']:
                resource_id = resource['id']
                self.log.info("Found Resource ID for: %s", resource['path'])
        return resource_id, parent_id

    def add_lambda_integration(self):
        """Attach lambda found to API."""
        lambda_uri = self.generate_uris()['lambda_uri']
        self.client.put_integration(
            restApiId=self.api_id,
            resourceId=self.resource_id,
            httpMethod=self.trigger_settings['method'],
            integrationHttpMethod='POST',
            uri=lambda_uri,
            type='AWS')
        self.add_integration_response()
        self.log.info("Successfully added Lambda intergration to API")

    def add_integration_response(self):
        """Add an intergation response to the API for the lambda integration."""
        self.client.put_integration_response(
            restApiId=self.api_id,
            resourceId=self.resource_id,
            httpMethod=self.trigger_settings['method'],
            statusCode='200',
            responseTemplates={'application/json': ''})

    def add_permission(self):
        """Add permission to Lambda for the API Trigger."""
        statement_id = '{}_api_{}'.format(self.app_name, self.trigger_settings['api_name'])
        principal = 'apigateway.amazonaws.com'
        lambda_alias_arn = get_lambda_alias_arn(self.app_name, self.env, self.region)
        lambda_unqualified_arn = get_lambda_arn(self.app_name, self.env, self.region)
        resource_name = self.trigger_settings.get('resource', '')
        resource_name = resource_name.replace('/', '')
        method_api_source_arn = 'arn:aws:execute-api:{}:{}:{}/{}/{}/{}'.format(
            self.region, self.account_id, self.api_id, self.env, self.trigger_settings['method'], resource_name)
        global_api_source_arn = 'arn:aws:execute-api:{}:{}:{}/*/*/{}'.format(self.region, self.account_id, self.api_id,
                                                                             resource_name)
        add_lambda_permissions(
            function=lambda_alias_arn,
            statement_id=statement_id + self.trigger_settings['method'],
            action='lambda:InvokeFunction',
            principal=principal,
            env=self.env,
            region=self.region,
            source_arn=method_api_source_arn)
        add_lambda_permissions(
            function=lambda_alias_arn,
            statement_id=statement_id,
            action='lambda:InvokeFunction',
            principal=principal,
            env=self.env,
            region=self.region,
            source_arn=global_api_source_arn)
        add_lambda_permissions(
            function=lambda_unqualified_arn,
            statement_id=statement_id + self.trigger_settings['method'],
            action='lambda:InvokeFunction',
            principal=principal,
            env=self.env,
            region=self.region,
            source_arn=method_api_source_arn)
        add_lambda_permissions(
            function=lambda_unqualified_arn,
            statement_id=statement_id,
            action='lambda:InvokeFunction',
            principal=principal,
            env=self.env,
            region=self.region,
            source_arn=global_api_source_arn)

    @retries(max_attempts=5, wait=2, exceptions=(botocore.exceptions.ClientError))
    def create_api_deployment(self):
        """Create API deployment of ENV name."""
        try:
            self.client.create_deployment(restApiId=self.api_id, stageName=self.env)
            self.log.info('Created a deployment resource.')
        except botocore.exceptions.ClientError as error:
            error_code = error.response['Error']['Code']
            if error_code == 'TooManyRequestsException':
                self.log.debug('Retrying. We have hit api limit.')
            else:
                self.log.debug('Retrying. We received %s.', error_code)

    def create_api_key(self):
        """Create API Key for API access."""
        apikeys = self.client.get_api_keys()
        for key in apikeys['items']:
            if key['name'] == self.app_name:
                self.log.info("Key %s already exists", self.app_name)
                break
        else:
            self.client.create_api_key(
                name=self.app_name, enabled=True, stageKeys=[{
                    'restApiId': self.api_id,
                    'stageName': self.env
                }])
            self.log.info("Successfully created API Key %s. Look in the AWS console for the key", self.app_name)

    def _format_base_path(self, api_name):
        """Format the base path name."""
        name = self.app_name
        if self.app_name != api_name:
            name = '{0}-{1}'.format(self.app_name, api_name)
        return name

    def update_api_mappings(self):
        """Create a cname for the API deployment."""
        response_provider = None
        response_action = None
        domain = self.generated.apigateway()['domain']
        try:
            response_provider = self.client.create_base_path_mapping(
                domainName=domain,
                basePath=self._format_base_path(self.trigger_settings['api_name']),
                restApiId=self.api_id,
                stage=self.env, )
            response_action = 'API mapping added.'
        except botocore.exceptions.ClientError as error:
            error_code = error.response['Error']['Code']
            if error_code == 'ConflictException':
                response_action = 'API mapping already exist.'
            else:
                response_action = 'Unknown error: {0}'.format(error_code)

        self.log.debug('Provider response: %s', response_provider)
        self.log.info(response_action)
        return response_provider

    def generate_uris(self):
        """Generate several lambda uris."""
        lambda_arn = "arn:aws:execute-api:{0}:{1}:{2}/*/{3}/{4}".format(self.region, self.account_id, self.api_id,
                                                                        self.trigger_settings['method'],
                                                                        self.trigger_settings['resource'])

        lambda_uri = ("arn:aws:apigateway:{0}:lambda:path/{1}/functions/"
                      "arn:aws:lambda:{0}:{2}:function:{3}/invocations").format(self.region, self.api_version,
                                                                                self.account_id, self.app_name)

        api_dns = "https://{0}.execute-api.{1}.amazonaws.com/{2}".format(self.api_id, self.region, self.env)

        uri_dict = {'lambda_arn': lambda_arn, 'lambda_uri': lambda_uri, 'api_dns': api_dns}
        return uri_dict

    def create_api(self):
        """Create the REST API."""
        created_api = self.client.create_rest_api(name=self.trigger_settings.get('api_name', self.app_name))
        api_id = created_api['id']
        self.log.info("Successfully created API")
        return api_id

    def create_resource(self, parent_id=""):
        """Create the specified resource.

        Args:
            parent_id (str): The resource ID of the parent resource in API Gateway
        """
        resource_name = self.trigger_settings.get('resource', '')
        resource_name = resource_name.replace('/', '')
        if not self.resource_id:
            created_resource = self.client.create_resource(
                restApiId=self.api_id, parentId=parent_id, pathPart=resource_name)
            self.resource_id = created_resource['id']
            self.log.info("Successfully created resource")
        else:
            self.log.info("Resource already exists. To update resource please delete existing resource: %s",
                          resource_name)

    def attach_method(self, resource_id):
        """Attach the defined method."""
        try:
            _response = self.client.put_method(
                restApiId=self.api_id,
                resourceId=resource_id,
                httpMethod=self.trigger_settings['method'],
                authorizationType="NONE",
                apiKeyRequired=False, )
            self.log.debug('Response for resource (%s) push authorization: %s', resource_id, _response)
            _response = self.client.put_method_response(
                restApiId=self.api_id,
                resourceId=resource_id,
                httpMethod=self.trigger_settings['method'],
                statusCode='200')
            self.log.debug('Response for resource (%s) no authorization: %s', resource_id, _response)

            self.log.info("Successfully attached method: %s", self.trigger_settings['method'])
        except botocore.exceptions.ClientError:
            self.log.info("Method %s already exists", self.trigger_settings['method'])

    def setup_lambda_api(self):
        """A wrapper for all the steps needed to setup the integration."""
        self.create_resource(self.parent_id)
        self.attach_method(self.resource_id)
        self.add_lambda_integration()
        self.add_permission()
        self.create_api_deployment()
        self.create_api_key()
        self.update_api_mappings()
