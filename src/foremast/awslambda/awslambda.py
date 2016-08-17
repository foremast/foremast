import logging
import os

import boto3

from ..exceptions import RequiredKeyNotFound
from ..utils import (get_role_arn, get_properties, get_details, get_subnets, get_security_group_id)

LOG = logging.getLogger(__name__)


class LambdaFunction(object):
    """Manipulate Lambda function"""

    def __init__(self, app, env, region, prop_path):
        """
        Lambda function object
        Args:
            app (str): Application name
            env (str): Environment/Account
            region (str): AWS Region
            prop_path (dict): Path of environment property file
        """
        self.app_name = app
        self.env = env
        self.region = region
        self.properties = get_properties(prop_path)
        generated = get_details(app=self.app_name)

        try:
            self.pipeline = self.properties['pipeline']['lambda']
        except KeyError:
            raise RequiredKeyNotFound("Lambda key in pipeline.json is required.")

        self.runtime = self.pipeline.get('runtime')
        self.description = self.pipeline.get('app_description')
        self.handler = self.pipeline.get('handler')

        if None in (self.runtime, self.description, self.handler):
            LOG.critical("Runtime, description and handler are required keys.")
            raise RequiredKeyNotFound('Runtime, description and handler are required keys.')

        self.vpc_enabled = self.pipeline.get('vpc_enabled', False)
        self.memory = self.properties.get('app', {}).get('memory', "128")
        self.timeout = self.properties.get('app', {}).get('timeout', "30")

        self.role_arn = get_role_arn(generated.iam()['role'], self.env, self.region)

        session = boto3.Session(profile_name=self.env, region_name=self.region)
        self.lambda_client = session.client('lambda')

    def _check_lambda(self):
        """Checks if lambda function exists
        Returns:
            True if function does exist
            False if function does not exist
        """
        list_lambda = self.lambda_client.list_functions()
        functions = list_lambda['Functions']

        for function in functions:
            if function['FunctionName'] == self.app_name:
                return True
        else:
            self.function_config = {}
            return False

    def _vpc_config(self):
        """Gets VPC config"""
        if self.vpc_enabled:
            subnets = get_subnets(env=self.env, region=self.region,
                                purpose='internal')['subnet_ids'][self.region]
            security_groups = self._get_sg_ids()

            vpc_config = {'SubnetIds': subnets, 'SecurityGroupIds': security_groups}
        else:
            vpc_config = {'SubnetIds': [], 'SecurityGroupIds': []}
        LOG.info("Lambda VPC config setup: %s", vpc_config)
        return vpc_config


    def _get_sg_ids(self):
        """get IDs for all defined security groups

        Returns:
            list: security group IDs for all lambda_extras
        """
        try:
            lambda_extras = self.properties[self.env]['security_groups']['lambda_extras']
        except KeyError:
            lambda_extras = []

        app_sg = get_security_group_id(name=self.app_name, env=self.env, region=self.region)
        sg_ids = [app_sg]
        for sg in lambda_extras:
            sg_id = get_security_group_id(name=sg, env=self.env, region=self.region)
            sg_ids.append(sg_id)
        return sg_ids


    def update_function(self):
        """Updates existing Lambda function configuration"""

        vpc_config = self._vpc_config()

        self.lambda_client.update_function_configuration(FunctionName=self.app_name,
                                                         Runtime=self.runtime,
                                                         Role=self.role_arn,
                                                         Handler=self.handler,
                                                         Description=self.description,
                                                         Timeout=int(self.timeout),
                                                         MemorySize=int(self.memory),
                                                         VpcConfig=vpc_config)

        LOG.info("Successfully updated Lambda function")

    def create_function(self):
        """Creates lambda function, configures lambda parameters"""

        # We need to upload non-zero zip when creating function
        # uploading hello_world python lambda function since AWS
        # doesn't care which executable is in ZIP
        here = os.path.dirname(os.path.realpath(__file__))
        dummyzip = "{}/dummylambda.zip".format(here)
        application_zip = open(dummyzip, 'rb').read()

        vpc_config = self._vpc_config()

        self.lambda_client.create_function(FunctionName=self.app_name,
                                           Runtime=self.runtime,
                                           Role=self.role_arn,
                                           Handler=self.handler,
                                           Code={
                                               'ZipFile': application_zip
                                           },
                                           Description=self.description,
                                           Timeout=int(self.timeout),
                                           MemorySize=int(self.memory),
                                           Publish=False,
                                           VpcConfig=vpc_config)

        LOG.info("Successfully created Lambda function")

    def create_lambda_function(self):
        """Creates or updates Lambda function"""
        if self._check_lambda():
            self.update_function()
        else:
            tself.create_function()
