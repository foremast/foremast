#   Foremast - Pipeline Tooling
#
#   Copyright 2016 Gogo, LLC
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

import logging
import zipfile

import boto3
from tryagain import retries

from ..exceptions import RequiredKeyNotFound
from ..utils import get_details, get_properties, get_role_arn, get_security_group_id, get_subnets

LOG = logging.getLogger(__name__)


class LambdaFunction(object):
    """Manipulate Lambda function."""

    def __init__(self, app, env, region, prop_path):
        """Lambda function object.

        Args:
            app (str): Application name
            env (str): Environment/Account
            region (str): AWS Region
            prop_path (str): Path of environment property file
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

        self.runtime = self.pipeline['runtime']
        self.description = self.pipeline['app_description']
        self.handler = self.pipeline['handler']
        self.vpc_enabled = self.pipeline['vpc_enabled']

        self.memory = self.properties[env]['app']['lambda_memory']
        self.timeout = self.properties[env]['app']['lambda_timeout']

        self.role_arn = get_role_arn(generated.iam()['role'], self.env, self.region)

        self.session = boto3.Session(profile_name=self.env, region_name=self.region)
        self.lambda_client = self.session.client('lambda')

    def _check_lambda(self):
        """Check if lambda function exists.

        Returns:
            True if function does exist
            False if function does not exist
        """
        exists = False
        try:
            self.lambda_client.get_function(FunctionName=self.app_name)
            exists = True
        except boto3.exceptions.botocore.exceptions.ClientError:
            pass
        return exists

    def _check_lambda_alias(self):
        """Check if lambda alias exists.

        Returns:
            True if alias exists
            False if alias does not exist
        """
        aliases = self.lambda_client.list_aliases(FunctionName=self.app_name)

        for alias in aliases['Aliases']:
            if alias['Name'] == self.env:
                LOG.info('Found alias %s for function %s', self.env, self.app_name)
                return True
        else:
            LOG.info('No alias %s found for function %s', self.env, self.app_name)
            return False

    def _vpc_config(self):
        """Get VPC config."""
        if self.vpc_enabled:
            subnets = get_subnets(env=self.env, region=self.region, purpose='internal')['subnet_ids'][self.region]
            security_groups = self._get_sg_ids()

            vpc_config = {'SubnetIds': subnets, 'SecurityGroupIds': security_groups}
        else:
            vpc_config = {'SubnetIds': [], 'SecurityGroupIds': []}
        LOG.debug("Lambda VPC config setup: %s", vpc_config)
        return vpc_config

    def _get_sg_ids(self):
        """Get IDs for all defined security groups.

        Returns:
            list: security group IDs for all lambda_extras
        """
        try:
            lambda_extras = self.properties[self.env]['security_groups']['lambda_extras']
        except KeyError:
            lambda_extras = []

        security_groups = [self.app_name] + lambda_extras
        sg_ids = []
        for sg in security_groups:
            sg_id = get_security_group_id(name=sg, env=self.env, region=self.region)
            sg_ids.append(sg_id)
        return sg_ids

    @retries(max_attempts=3, wait=1, exceptions=(boto3.exceptions.botocore.exceptions.ClientError))
    def create_alias(self):
        """Create lambda alias with env name and points it to $LATEST."""
        LOG.info('Creating alias %s', self.env)

        try:
            self.lambda_client.create_alias(
                FunctionName=self.app_name,
                Name=self.env,
                FunctionVersion='$LATEST',
                Description='Alias for {}'.format(self.env)
            )
        except boto3.exceptions.botocore.exceptions.ClientError as error:
            LOG.debug('Create alias error: %s', error)
            LOG.info("Alias creation failed. Retrying...")
            raise

    @retries(max_attempts=3, wait=1, exceptions=(boto3.exceptions.botocore.exceptions.ClientError))
    def update_alias(self):
        """Update lambda alias to point to $LATEST."""
        LOG.info('Updating alias %s to point to $LATEST', self.env)

        try:
            self.lambda_client.update_alias(
                FunctionName=self.app_name,
                Name=self.env,
                FunctionVersion='$LATEST'
            )
        except boto3.exceptions.botocore.exceptions.ClientError as error:
            LOG.debug('Update alias error: %s', error)
            LOG.info("Alias update failed. Retrying...")
            raise

    @retries(max_attempts=3, wait=1, exceptions=(SystemExit))
    def update_function_configuration(self, vpc_config):
        """Update existing Lambda function configuration.

        Args:
            vpc_config (dict): Dictionary of SubnetIds and SecurityGroupsIds for using
                               a VPC in lambda
        """
        LOG.info('Updating configuration for lambda function: %s', self.app_name)

        try:
            self.lambda_client.update_function_configuration(
                FunctionName=self.app_name,
                Runtime=self.runtime,
                Role=self.role_arn,
                Handler=self.handler,
                Description=self.description,
                Timeout=int(self.timeout),
                MemorySize=int(self.memory),
                VpcConfig=vpc_config)
        except boto3.exceptions.botocore.exceptions.ClientError as error:
            if 'CreateNetworkInterface' in error.response['Error']['Message']:
                message = '{0} is missing "ec2:CreateNetworkInterface"'.format(self.role_arn)
                LOG.debug(message)
                raise SystemExit(message)

            raise

        LOG.info("Successfully updated Lambda configuration.")

    @retries(max_attempts=3, wait=1, exceptions=(SystemExit))
    def create_function(self, vpc_config):
        """Create lambda function, configures lambda parameters.

        We need to upload non-zero zip when creating function. Uploading
        hello_world python lambda function since AWS doesn't care which
        executable is in ZIP.

        Args:
            vpc_config (dict): Dictionary of SubnetIds and SecurityGroupsIds for using
                               a VPC in lambda
        """
        zip_file = 'lambda-holder.zip'
        with zipfile.ZipFile(zip_file, mode='w') as z:
            z.writestr('index.py', 'print "Hello world"')

        contents = ''
        with open('lambda-holder.zip', 'rb') as openfile:
            contents = openfile.read()

        LOG.info('Creating lambda function: %s', self.app_name)

        try:
            self.lambda_client.create_function(
                FunctionName=self.app_name,
                Runtime=self.runtime,
                Role=self.role_arn,
                Handler=self.handler,
                Code={
                    'ZipFile': contents
                },
                Description=self.description,
                Timeout=int(self.timeout),
                MemorySize=int(self.memory),
                Publish=False,
                VpcConfig=vpc_config)
        except boto3.exceptions.botocore.exceptions.ClientError as error:
            if 'CreateNetworkInterface' in error.response['Error']['Message']:
                message = '{0} is missing "ec2:CreateNetworkInterface"'.format(self.role_arn)
                LOG.critical(message)
                raise SystemExit(message)

            raise

        LOG.info("Successfully created Lambda function and alias")

    def create_lambda_function(self):
        """Create or update Lambda function."""
        vpc_config = self._vpc_config()

        if self._check_lambda():
            self.update_function_configuration(vpc_config)
        else:
            self.create_function(vpc_config)

        if self._check_lambda_alias():
            self.update_alias()
        else:
            self.create_alias()
