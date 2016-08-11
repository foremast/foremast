import logging
import boto3

from ..utils import (InvalidEventConfiguration, get_lambda_arn.
                     get_details, get_properties)

LOG = logging.getLogger(__name__)

class APIGateway:

    def __init__(self,
                 app='',
                 env='',
                 region='',
                 prop_path=''):
        self.log = logging.getLogger(__name__)
        self.generated = get_details(app=app)
        self.app_name = self.gernerated.app_name()
        self.settings = get_properties(prop_path)
        self.env = env
        self.client = boto3.Session(profile_name=env, region_name=region)
        self.trigger_settings = self.get_trigger_config()

    def get_trigger_config(self):
        for trigger in self.settings[self.env]['lambda_triggers']:
            if trigger['type'] == 'api-gateway':
                return trigger

    def find_api_id(self):
        allapis = self.client.get_rest_apis()
        api_name = self.settings[self.env]['lambda_triggers']
        for api in allapis['items']:
            if api['name'] == self.trigger_settings['api_name']:
                self.api_id = api['id']
                break

    def find_resource_id(self):
        all_resources = self.client.get_resources(restApiId=self.api_id)
        for resource in all_resources['items']:
            if resource['path'] == self.trigger_settings['resource']
                self.resource_id = resource['id']
                break

    def add_lambda_intergration(self):
        lambda_uri = "arn:aws:apigateway:{0}:lambda:path/{1}/functions/arn:aws:lambda:{0}:{2}:function:{3}/invocations".format(region, APIVERSION, ACCOUNT_ID, self.app_name)
        self.client.put_integration(
                        restApiId = self.api_id,
                        resourceId = self.resource_id
                        httpMethod = self.trigger_settings['method'],
                        integrationHttpMethod = self.trigger_settings['method'],
                        uri = lambda_uri,
                        type = 'AWS'
                    )

    def deploy_stage():
        return

    def create_api_key();
        return

    def update_dns();
        return

#    def create_api(self):
#        created_api = self.client.create_rest_api(
#                                  name=self.trigger_settings['api_name'],
#                                  description=self.settings[self.env]['lambda']['app_description']
#                              )
#        self.api_id = created_api['id']



