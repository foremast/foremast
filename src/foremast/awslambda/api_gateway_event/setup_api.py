import logging
import uuid

import boto3
from foremast.utils import (InvalidEventConfiguration, get_details,
                            get_env_credential, get_lambda_arn, get_properties)

LOG = logging.getLogger(__name__)


class APIGateway:
    """Class to handle API Gateway and Lambda integration.

    Args:
        app (str): Application Name
        env (str): Environment/account for deployments
        region (str): AWS Region
        prop_path (str): Path to the raw.properties.json
    """

    def __init__(self, app='', env='', region='', rules=''):
        self.log = logging.getLogger(__name__)
        self.generated = get_details(app=app)
        self.trigger_settings = rules
        self.app_name = self.generated.app_name()
        self.env = env
        self.region = region
        session = boto3.Session(profile_name=env, region_name=region)
        self.client = session.client('apigateway')

    def create_api(self):
        created_api = self.client.create_rest_api(
                                  name=self.trigger_settings.get('api_name', default=self.app_name)
                              )
        self.api_id = created_api['id']
        return self.api_id

    def create_resource(self, parentId=None):
        created_resource = self.client.create_resource(
                                    restApiId = self.api_id,
                                    parentId = parentId,
                                    pathPart = self.rules['resource']
                                    )
        self.resource_id = created_resource['id']
        return self.resource_id

    def attach_method(self):
        self.client.put_method(
                        restApiId = self.api_id,
                        resourceId = self.resource_id,
                        httpMethod = self.rules['method'],
                        authorizationType = SOMETHING,
                        apiKeyRequired = True,
                        )




if __name__ == "__main__":
    gateway = APIGateway(app='dougtest', env='sandbox', region='us-east-1')
    gateway.setup_lambda_api()
