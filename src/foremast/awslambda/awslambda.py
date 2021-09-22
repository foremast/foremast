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
"""Create lambda functions"""

import logging
import zipfile

import boto3
from tryagain import retries

from ..exceptions import RequiredKeyNotFound
from ..utils import get_details, get_lambda_arn, get_properties, get_role_arn, get_security_group_id, get_subnets

LOG = logging.getLogger(__name__)


class LambdaFunction:
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
        self.group = generated.data['project']

        try:
            self.pipeline = self.properties['pipeline']['lambda']
        except KeyError:
            raise RequiredKeyNotFound("Lambda key in pipeline.json is required.")

        self.runtime = self.pipeline['runtime']
        self.description = self.pipeline['app_description']
        self.handler = self.pipeline['handler']
        self.vpc_enabled = self.pipeline['vpc_enabled']

        self.settings = get_properties(prop_path, env=self.env, region=self.region)
        app = self.settings['app']
        self.custom_tags = app['custom_tags']
        self.lambda_environment = app['lambda_environment']
        self.lambda_layers = app['lambda_layers']
        self.lambda_destinations = app['lambda_destinations']
        self.lambda_dlq = app['lambda_dlq']
        self.lambda_filesystems = app['lambda_filesystems']
        self.lambda_tracing = app['lambda_tracing']
        self.lambda_provisioned_throughput = app['lambda_provisioned_throughput']
        self.memory = app['lambda_memory']
        self.role = app.get('lambda_role') or generated.iam()['lambda_role']
        self.timeout = app['lambda_timeout']
        self.concurrency_limit = app.get('lambda_concurrency_limit')
        self.subnet_purpose = app['lambda_subnet_purpose']
        self.subnet_count = app['lambda_subnet_count']

        self.role_arn = get_role_arn(self.role, self.env, self.region)

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

        matched_alias = False
        for alias in aliases['Aliases']:
            if alias['Name'] == self.env:
                LOG.info('Found alias %s for function %s', self.env, self.app_name)
                matched_alias = True
                break
        else:
            LOG.info('No alias %s found for function %s', self.env, self.app_name)
        return matched_alias

    def _vpc_config(self):
        """Get VPC config."""
        if self.vpc_enabled:
            subnets_data = get_subnets(env=self.env, region=self.region, purpose=self.subnet_purpose)
            subnets = subnets_data['subnet_ids'][self.region]
            if self.subnet_count:
                subnets = subnets[:self.subnet_count]
                LOG.info('Subnet Count of %s specified. Limiting to subnets: %s', self.subnet_count, subnets)

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
            lambda_extras = self.settings['security_groups']['lambda_extras']
        except KeyError:
            lambda_extras = []

        security_groups = [self.app_name] + lambda_extras
        sg_ids = []
        for security_group in security_groups:
            sg_id = get_security_group_id(name=security_group, env=self.env, region=self.region)
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
                Description='Alias for {}'.format(self.env))
        except boto3.exceptions.botocore.exceptions.ClientError as error:
            LOG.debug('Create alias error: %s', error)
            LOG.info("Alias creation failed. Retrying...")
            raise

    @retries(max_attempts=3, wait=1, exceptions=(boto3.exceptions.botocore.exceptions.ClientError))
    def update_alias(self):
        """Update lambda alias to point to $LATEST."""
        LOG.info('Updating alias %s to point to $LATEST', self.env)

        try:
            self.lambda_client.update_alias(FunctionName=self.app_name, Name=self.env, FunctionVersion='$LATEST')
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

        default_tags = {'app_group': self.group, 'app_name': self.app_name}
        lambda_tags = {**default_tags, **self.custom_tags}

        try:
            self.lambda_client.update_function_configuration(
                Environment=self.lambda_environment,
                FunctionName=self.app_name,
                Runtime=self.runtime,
                Role=self.role_arn,
                Handler=self.handler,
                Description=self.description,
                Timeout=int(self.timeout),
                MemorySize=int(self.memory),
                VpcConfig=vpc_config,
                Layers=self.lambda_layers,
                DeadLetterConfig=self.lambda_dlq,
                TracingConfig=self.lambda_tracing,
                FileSystemConfigs=self.lambda_filesystems)

            if self.concurrency_limit:
                self.lambda_client.put_function_concurrency(
                    FunctionName=self.app_name,
                    ReservedConcurrentExecutions=self.concurrency_limit
                )
            else:
                self.lambda_client.delete_function_concurrency(FunctionName=self.app_name)

            if self.lambda_destinations:
                self.lambda_client.put_function_event_invoke_config(
                    FunctionName=self.app_name,
                    DestinationConfig=self.lambda_destinations
                )

            if self.lambda_provisioned_throughput:
                self.lambda_client.put_provisioned_concurrency_config(
                    FuctionName=self.app_name,
                    Qualifier=self.env,
                    ProvisionedConcurrentExecutions=self.lambda_provisioned_throughput)
            else:
                self.lambda_client.delete_provisioned_concurrency_config(
                    FunctionName=self.app_name,
                    Qualifier=self.env)

        except boto3.exceptions.botocore.exceptions.ClientError as error:
            if 'CreateNetworkInterface' in error.response['Error']['Message']:
                message = '{0} is missing "ec2:CreateNetworkInterface"'.format(self.role_arn)
                LOG.debug(message)
                raise SystemExit(message)

            raise
        LOG.info('Updating Lambda function tags')

        lambda_arn = get_lambda_arn(self.app_name, self.env, self.region)
        self.lambda_client.tag_resource(Resource=lambda_arn, Tags=lambda_tags)

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
        with zipfile.ZipFile(zip_file, mode='w') as zipped:
            zipped.writestr('index.py', 'print "Hello world"')

        contents = ''
        with open('lambda-holder.zip', 'rb') as openfile:
            contents = openfile.read()

        LOG.info('Creating lambda function: %s', self.app_name)

        default_tags = {'app_group': self.group, 'app_name': self.app_name}
        lambda_tags = {**default_tags, **self.custom_tags}

        try:
            self.lambda_client.create_function(
                Environment=self.lambda_environment,
                FunctionName=self.app_name,
                Runtime=self.runtime,
                Role=self.role_arn,
                Handler=self.handler,
                Code={'ZipFile': contents},
                Description=self.description,
                Timeout=int(self.timeout),
                MemorySize=int(self.memory),
                Publish=False,
                VpcConfig=vpc_config,
                Tags=lambda_tags,
                Layers=self.lambda_layers,
                DeadLetterConfig=self.lambda_dlq,
                TracingConfig=self.lambda_tracing,
                FileSystemConfigs=self.lambda_filesystems)

            if self.lambda_destinations:
                self.lambda_client.put_function_event_invoke_config(
                    FunctionName=self.app_name,
                    DestinationConfig=self.lambda_destinations
                )

            if self.lambda_provisioned_throughput:
                self.lambda_client.put_provisioned_concurrency_config(
                    FuctionName=self.app_name,
                    Qualifier=self.env,
                    ProvisionedConcurrentExecutions=self.lambda_provisioned_throughput)

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
