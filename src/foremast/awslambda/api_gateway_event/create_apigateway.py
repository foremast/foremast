import logging
import boto3
import uuid

from foremast.utils import (InvalidEventConfiguration, get_lambda_arn,
                     get_details, get_properties, get_env_credential)

LOG = logging.getLogger(__name__)

class APIGateway:
    """Class to handle API Gateway and Lambda integration

    Args:
        app (str): Application Name
        env (str): Environment/account for deployments
        region (str): AWS Region
        prop_path (str): Path to the raw.properties.json
    """
    def __init__(self,
                 app='',
                 env='',
                 region='',
                 prop_path=''):
        self.log = logging.getLogger(__name__)
        self.generated = get_details(app=app)
        self.app_name = self.gernerated.app_name()
        self.settings = get_properties(prop_path)
        self.account_id = get_env_credential(env=self.env)['accountId']
        self.env = env
        self.region = region
        session = boto3.Session(profile_name=env, region_name=region)
        self.client = session.client('apigateway')
        self.lambda_client = session.client('lambda')
        self.trigger_settings = self.get_trigger_config()

    def get_trigger_config(self):
        """Searches the settings for api lambda triggers

        Returns:
            dict: configuration values of the trigger
        """
        for trigger in self.settings[self.env]['lambda_triggers']:
            if trigger['type'] == 'api-gateway':
                return trigger

    def find_api_id(self):
        """Given API name, finds API ID"""
        allapis = self.client.get_rest_apis()
        api_name = self.settings[self.env]['lambda_triggers']
        for api in allapis['items']:
            if api['name'] == api_name:
                self.api_id = api['id']
                self.log.info("Found API for: %s", api_name)
                break
        else:
            self.log.critical("No API %s found", api_name)

    def find_resource_id(self):
        """Given a resource path and API Id, finds resource Id"""
        all_resources = self.client.get_resources(restApiId=self.api_id)
        for resource in all_resources['items']:
            if resource['path'] == self.trigger_settings['resource']:
                self.resource_id = resource['id']
                self.log.info("Found Resource ID for: %s", resource['path'])
                break
        else:
            self.log.critical("No resource found matching %s", "/")

    def add_lambda_integration(self):
        """Attaches lambda found to API"""
        api_version = self.lambda_client.meta.service_model.api_version
        lambda_uri = "arn:aws:apigateway:{0}:lambda:path/{1}/functions/arn:aws:lambda:{0}:{2}:function:{3}/invocations".format(self.region, api_version, self.account_id, self.app_name)
        self.client.put_integration(
                        restApiId = self.api_id,
                        resourceId = self.resource_id,
                        httpMethod = self.trigger_settings['method'],
                        integrationHttpMethod = 'POST',
                        uri = lambda_uri,
                        type = 'AWS'
                    )
        self.add_integration_response()
        self.log.info("Successfully added Lambda intergration to API")

    def add_integration_response(self):
        """Adds an intergation response to the API for the lambda integration"""
        self.client.put_integration_response(
                        restApiId = self.api_id,
                        resourceId = self.resource_id,
                        httpMethod = self.trigger_settings['method'],
                        statusCode = '200',
                        responseTemplates={'application/json': ''}
                    )

    def add_lambda_permission(self):
        """Adds permission to Lambda for the API Trigger"""
        arn = "arn:aws:execute-api:{0}:{1}:{2}/*/{3}/{4}".format(
                self.region, self.account_id, self.api_id,
                self.trigger_settings['method'],
                self.trigger_settings['resource'])
        self.lambda_client.add_permission(
                        FunctionName=self.app_name,
                        StatementId=uuid.uuid4().hex,
                        Action='lambda:InvokeFunction',
                        Principal='apigateway.amazonaws.com',
                        SourceArn = arn
                    )
        self.log.info("Successfully updated lambda permissions for API")

    def create_api_deployment(self):
        """Creates API deployment of ENV name"""
        deployment = self.client.create_deployment(
                restApiId = self.api_id,
                stageName = self.env)

    def create_api_key(self):
        """Creates API Key for API access"""
        apikeys = self.client.get_api_keys()
        for key in apikeys['items']:
            if key['name'] == self.app_name:
                self.log.info("Key %s already exists", self.app_name)
                break
        else:
            self.client.create_api_key(
                    name=self.app_name,
                    enabled=True,
                    stageKeys = [
                        {
                            'restApiId': self.api_id,
                            'stageName': self.env
                        }
                    ]
                )
            self.log.info("Successfully created API Key %s. Look in the AWS console for the key",
                    self.app_name)

    def update_dns(self):
        """Creates a cname for the API deployment"""
        dns_name = "https://{0}.execute-api.{1}.amazonaws.com/{2}".format(
                self.api_id, self.region, self.env)
        print(dns_name)

    def setup_lambda_api(self):
        """A wrapper for all the steps needed to setup the integration"""
        self.find_api_id()
        self.find_resource_id()
        self.add_lambda_integration()
        self.add_lambda_permission()
        self.create_api_deployment()
        self.create_api_key()
        self.update_dns()

#    def create_api(self):
#        created_api = self.client.create_rest_api(
#                                  name=self.trigger_settings['api_name'],
#                                  description=self.settings[self.env]['lambda']['app_description']
#                              )
#        self.api_id = created_api['id']


if __name__ == "__main__":
    gateway = APIGateway(app='dougtest', env='sandbox', region='us-east-1')
    gateway.setup_lambda_api()
