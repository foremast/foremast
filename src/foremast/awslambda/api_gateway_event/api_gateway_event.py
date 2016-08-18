import logging
import uuid

import boto3
import botocore

from foremast.exceptions import InvalidEventConfiguration
from foremast.utils import (get_details, get_env_credential, get_dns_zone_ids,
                            update_dns_zone_record, get_properties)


class APIGateway:
    """Class to handle API Gateway and Lambda integration.

    Args:
        app (str): Application Name
        env (str): Environment/account for deployments
        region (str): AWS Region
        rules (str): Trigger settings
        prop_path (str): Path to the raw.properties.json
    """

    def __init__(self, app='', env='', region='', rules='', prop_path=''):
        self.log = logging.getLogger(__name__)
        self.generated = get_details(app=app)
        self.trigger_settings = rules
        self.app_name = self.generated.app_name()
        self.env = env
        self.account_id = get_env_credential(env=self.env)['accountId']
        self.region = region
        self.properties = get_properties(properties_file=prop_path, env=self.env)

        session = boto3.Session(profile_name=env, region_name=region)
        self.client = session.client('apigateway')
        self.lambda_client = session.client('lambda')
        self.api_version = self.lambda_client.meta.service_model.api_version

    def find_api_id(self):
        """Given API name, find API ID."""
        allapis = self.client.get_rest_apis()
        api_name = self.trigger_settings['api_name']
        for api in allapis['items']:
            if api['name'] == api_name:
                self.api_id = api['id']
                self.log.info("Found API for: %s", api_name)
                break
        else:
            raise InvalidEventConfiguration("API does not exist: {}".format(api_name))

    def find_resource_id(self):
        """Given a resource path and API Id, find resource Id."""
        all_resources = self.client.get_resources(restApiId=self.api_id)
        for resource in all_resources['items']:
            if resource['path'] == self.trigger_settings['resource']:
                self.resource_id = resource['id']
                self.log.info("Found Resource ID for: %s", resource['path'])
                break
        else:
            raise InvalidEventConfiguration("Resource does not exist: {}".format(self.trigger_settings['resource']))

    def add_lambda_integration(self):
        """Attach lambda found to API."""
        lambda_uri = self.generate_uris()['lambda_uri']
        self.client.put_integration(restApiId=self.api_id,
                                    resourceId=self.resource_id,
                                    httpMethod=self.trigger_settings['method'],
                                    integrationHttpMethod='POST',
                                    uri=lambda_uri,
                                    type='AWS')
        self.add_integration_response()
        self.log.info("Successfully added Lambda intergration to API")

    def add_integration_response(self):
        """Add an intergation response to the API for the lambda integration."""
        self.client.put_integration_response(restApiId=self.api_id,
                                             resourceId=self.resource_id,
                                             httpMethod=self.trigger_settings['method'],
                                             statusCode='200',
                                             responseTemplates={'application/json': ''})

    def add_lambda_permission(self):
        """Add permission to Lambda for the API Trigger."""
        lambda_arn = self.generate_uris()['lambda_arn']
        response_action = None
        statement_id = 'add_permission_for_{}'.format(
            self.trigger_settings['api_name'],
        )
        try:
            self.lambda_client.add_permission(FunctionName=self.app_name,
                                              StatementId=statement_id,
                                              Action='lambda:InvokeFunction',
                                              Principal='apigateway.amazonaws.com',
                                              SourceArn=lambda_arn)
            response_action = 'Add permission with Sid: {}'.format(statement_id)
        except botocore.exceptions.ClientError:
            response_action = 'Did not add any permissions.'

        self.log.debug('Related StatementId (SID): %s', statement_id)
        self.log.info(response_action)

    def create_api_deployment(self):
        """Create API deployment of ENV name."""
        try:
            self.client.create_deployment(restApiId=self.api_id, stageName=self.env)
        except botocore.exceptions.ClientError:
            self.log.debug('We should retry create_deployment. We have hit api limit.')

    def create_api_key(self):
        """Create API Key for API access."""
        apikeys = self.client.get_api_keys()
        for key in apikeys['items']:
            if key['name'] == self.app_name:
                self.log.info("Key %s already exists", self.app_name)
                break
        else:
            self.client.create_api_key(name=self.app_name,
                                       enabled=True,
                                       stageKeys=[
                                           {
                                               'restApiId': self.api_id,
                                               'stageName': self.env
                                           }
                                       ])
            self.log.info("Successfully created API Key %s. Look in the AWS console for the key", self.app_name)

    def update_dns(self):
        """Create a cname for the API deployment."""
        dns = {
            'dns_name': self.generate_uris()['api_dns'],
            'dns_ttl': self.properties['dns']['ttl'],
            'dns_public': self.trigger_settings.get('public', False),
        }

        facing = 'internal'
        if dns['dns_public']:
            facing = 'external'

        zone_ids = get_dns_zone_ids(env=self.env, facing=facing)

        for zone_id in zone_ids:
            self.log.debug('zone_id: %s', zone_id)
            response = update_dns_zone_record(self.env, zone_id, **dns)
            self.log.debug('Dns upsert response: %s', response)
        return response

    def generate_uris(self):
        lambda_arn = "arn:aws:execute-api:{0}:{1}:{2}/*/{3}/{4}".format(self.region, self.account_id, self.api_id,
                                                                 self.trigger_settings['method'],
                                                                 self.trigger_settings['resource'])

        lambda_uri = ("arn:aws:apigateway:{0}:lambda:path/{1}/functions/"
                      "arn:aws:lambda:{0}:{2}:function:{3}/invocations").format(self.region, self.api_version,
                                                                                self.account_id, self.app_name)

        api_dns = "https://{0}.execute-api.{1}.amazonaws.com/{2}".format(self.api_id, self.region, self.env)

        uri_dict = { 'lambda_arn': lambda_arn,
                     'lambda_uri': lambda_uri,
                     'api_dns': api_dns
                   }
        return uri_dict

    def setup_lambda_api(self):
        """A wrapper for all the steps needed to setup the integration."""
        self.find_api_id()
        self.find_resource_id()
        self.add_lambda_integration()
        self.add_lambda_permission()
        self.create_api_deployment()
        self.create_api_key()
        self.update_dns()

if __name__ == "__main__":
    gateway = APIGateway(app='dougtest', env='sandbox', region='us-east-1')
    gateway.setup_lambda_api()
