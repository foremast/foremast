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
from os.path import exists

import boto3
from tryagain import retries

from ..consts import LAMBDA_STANDALONE_MODE
from ..exceptions import RequiredKeyNotFound
from ..utils import get_details, get_lambda_arn, get_properties, get_role_arn, get_security_group_id, get_subnets

LOG = logging.getLogger(__name__)


class LambdaFunction:
    """Manipulate Lambda function."""

    def __init__(self, app, env, region, prop_path, artifact_path):
        """Lambda function object.

        Args:
            app (str): Application name
            env (str): Environment/Account
            region (str): AWS Region
            prop_path (str): Path of environment property file
            artifact_path (str): Path or URI for code artifact
        """
        self.app_name = app
        self.env = env
        self.region = region
        self.properties = get_properties(prop_path)
        generated = get_details(app=self.app_name)
        self.group = generated.data['project']
        self.artifact_path = artifact_path

        try:
            self.pipeline = self.properties['pipeline']['lambda']
        except KeyError:
            raise RequiredKeyNotFound("Lambda key in pipeline.json is required.")

        self.runtime = self.pipeline['runtime']
        self.description = self.pipeline['app_description']
        self.handler = self.pipeline['handler']
        self.vpc_enabled = self.pipeline['vpc_enabled']
        self.package_type = "zip" if 'package_type' not in self.pipeline else self.pipeline['package_type']

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
        try:
            self.lambda_client.get_function(FunctionName=self.app_name)
            return True
        except boto3.exceptions.botocore.exceptions.ClientError:
            return False

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

    @retries(max_attempts=3, wait=1, exceptions=boto3.exceptions.botocore.exceptions.ClientError)
    def _create_alias(self):
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

    @retries(max_attempts=3, wait=1, exceptions=boto3.exceptions.botocore.exceptions.ClientError)
    def _update_alias(self):
        """Update lambda alias to point to $LATEST."""
        LOG.info('Updating alias %s to point to $LATEST', self.env)

        try:
            self.lambda_client.update_alias(FunctionName=self.app_name, Name=self.env, FunctionVersion='$LATEST')
        except boto3.exceptions.botocore.exceptions.ClientError as error:
            LOG.debug('Update alias error: %s', error)
            LOG.info("Alias update failed. Retrying...")
            raise

    @retries(max_attempts=3, wait=1, exceptions=SystemExit)
    def _update_function_configuration(self, vpc_config):
        """Update existing Lambda function configuration.

        Args:
            vpc_config (dict): Dictionary of SubnetIds and SecurityGroupsIds for using
                               a VPC in lambda
        """
        LOG.info('Updating configuration for lambda function: %s', self.app_name)

        default_tags = {'app_group': self.group, 'app_name': self.app_name}
        lambda_tags = {**default_tags, **self.custom_tags}

        try:
            lambda_args = self._get_lambda_args("update", vpc_config, lambda_tags)
            self.lambda_client.update_function_configuration(**lambda_args)

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

    @retries(max_attempts=3, wait=1, exceptions=SystemExit)
    def _create_function(self, vpc_config):
        """Create lambda function, configures lambda parameters.

        We need to upload non-zero zip when creating function. Uploading
        hello_world python lambda function since AWS doesn't care which
        executable is in ZIP.

        Args:
            vpc_config (dict): Dictionary of SubnetIds and SecurityGroupsIds for using
                               a VPC in lambda
        """
        LOG.info('Creating lambda function: %s', self.app_name)

        default_tags = {'app_group': self.group, 'app_name': self.app_name}
        lambda_tags = {**default_tags, **self.custom_tags}

        try:
            lambda_args = self._get_lambda_args("create", vpc_config, lambda_tags)
            self.lambda_client.create_function(**lambda_args)

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

    def deploy_lambda_function(self):
        """Create or update Lambda function."""
        vpc_config = self._vpc_config()

        if self._check_lambda():
            self._update_function_configuration(vpc_config)
        else:
            self._create_function(vpc_config)

        if self._check_lambda_alias():
            self._update_alias()
        else:
            self._create_alias()

    def _get_lambda_args(self, action, vpc_config, lambda_tags):
        """Gets lambda args as a dictionary, depending on properties such as package_type.
        Args:
            action (str): Action taken place, either create or update.  This adjust the
                          outputted dictionary and it's keys
        """
        # Default args that apply to all package types
        lambda_args = {
            "Environment": self.lambda_environment,
            "FunctionName": self.app_name,
            "Role": self.role_arn,
            "Description":  self.description,
            "Timeout": int(self.timeout),
            "MemorySize": int(self.memory),
            "VpcConfig": vpc_config,
            "Layers": self.lambda_layers,
            "DeadLetterConfig": self.lambda_dlq,
            "TracingConfig": self.lambda_tracing,
            "FileSystemConfigs": self.lambda_filesystems,
        }

        if action == "create":
            lambda_args["Publish"] = True if LAMBDA_STANDALONE_MODE else False
            lambda_args["PackageType"] = self.package_type.capitalize()
            lambda_args["Tags"] = lambda_tags
            lambda_args["Code"] = self._get_default_lambda_code()

        # Args for zip packages only
        if self.package_type.lower() == "zip":
            lambda_args["Runtime"] = self.runtime
            lambda_args["Handler"] = self.handler

        return lambda_args

    def _get_default_lambda_code(self):
        if self.package_type.lower() == "zip":
            return self._get_default_lambda_code_zip()
        elif self.package_type.lower() == "image":
            return {'ImageUri': self.artifact_path}
        else:
            raise Exception("Invalid Lambda package_type: " + self.package_type)

    def _get_default_lambda_code_zip(self):
        if LAMBDA_STANDALONE_MODE:
            if self.artifact_path and exists(self.artifact_path):
                with open(self.artifact_path, 'rb') as openfile:
                    contents = openfile.read()
                    return {'ZipFile': contents}
            raise Exception("Artifact file '{}' not found.  Note: You must download and pass in a local address"
                            .format(self.artifact_path))
        else:
            return {'ZipFile': self._create_dummy_zip_package()}

    def _create_dummy_zip_package(self):
        """When lambda's are created during foremast infra step, we must create a dummy zip as a placeholder
        until the real code is added in next Spinnaker step.  This does not apply if using feature flag
        LAMBDA_STANDALONE_MODE=True."""
        LOG.info("Creating dummy zip package and overriding artifact path")
        self.artifact_path = 'lambda-holder.zip'
        with zipfile.ZipFile(self.artifact_path, mode='w') as zipped:
            zipped.writestr('index.py', 'print "Hello world"')
        with open('lambda-holder.zip', 'rb') as openfile:
            return openfile.read()
