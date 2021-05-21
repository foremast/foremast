#   Foremast - Pipeline Tooling
#
#   Copyright 2021 Redbox Automated Retail, LLC
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
"""Create AWS Step Functions"""

import logging

import json
import boto3

from ..utils import get_details, get_properties, get_role_arn

LOG = logging.getLogger(__name__)


class AWSStepFunction:
    """Manipulate Step Function."""

    def __init__(self, app=None, env=None, region='us-east-1', prop_path=None):
        """AWS Step Function object.

        Args:
            app (str): Application name
            env (str): Environment/Account
            region (str): AWS Region
            prop_path (str): Path of environment property file
        """
        self.app_name = app
        self.env = env
        self.region = region
        self.properties = get_properties(prop_path, env=self.env, region=self.region)
        self.stepfunction_data = self.properties['stepfunction']
        self.custom_tags = self.properties['app']['custom_tags']
        generated = get_details(app=self.app_name)
        self.group = generated.data['project']

        session = boto3.Session(profile_name=self.env, region_name=self.region)
        self.client = session.client('stepfunctions')

        self.state_machine_arn = None
        self.role = generated.iam()['role']
        self.role_arn = get_role_arn(self.role, self.env, self.region)

    def create_stepfunction(self):
        """Creates the Step Function if it does not already exist

        Returns:
                dict: the response of the Boto3 command
        """

        stepfunction_tags = [
            {'key': 'app_group', 'value': self.group},
            {'key': 'app_name', 'value': self.app_name}
        ]

        for each_tag in self.custom_tags:
            stepfunction_tags.append({'key': each_tag, 'value': self.custom_tags[each_tag]})

        self.role_arn = get_role_arn(self.role, self.env, self.region)

        if not self.find_stepfunction_arn():
            response = self.client.create_state_machine(
                name=self.stepfunction_data.get('name', self.app_name),
                definition=json.dumps(self.stepfunction_data['json_definition']),
                roleArn=self.role_arn,
                type=self.stepfunction_data['statemachine_type'],
                loggingConfiguration=self.stepfunction_data['logging_configuration'],
                tags=stepfunction_tags,
                tracingConfiguration=self.stepfunction_data['tracing'])
            LOG.debug(response)

            self.state_machine_arn = response.get('stateMachineArn')

            LOG.info("Successfully configured Step Function - %s", self.app_name)
        else:
            response = self.update_stepfunction_definition()

        return response

    def update_stepfunction_definition(self):
        """Translates the json definition and puts it on created Step Function

        Returns:
                dict: the response of the Boto3 command
        """

        stepfunction_tags = [
            {'key': 'app_group', 'value': self.group},
            {'key': 'app_name', 'value': self.app_name}
        ]

        for each_tag in self.custom_tags:
            stepfunction_tags.append({'key': each_tag, 'value': self.custom_tags[each_tag]})

        if not self.state_machine_arn:
            self.find_stepfunction_arn()

        response = self.client.update_state_machine(
            stateMachineArn=self.state_machine_arn,
            definition=json.dumps(self.stepfunction_data['json_definition']),
            roleArn=self.role_arn,
            loggingConfiguration=self.stepfunction_data['logging_configuration'],
            tracingConfiguration=self.stepfunction_data['tracing'])
        LOG.debug(response)
        LOG.info("Successfully updated Step Function State Machine definition")

        LOG.info('Updating Step Function tags')

        self.client.tag_resource(resourceArn=self.state_machine_arn, tags=stepfunction_tags)

        return response

    def find_stepfunction_arn(self):
        """Finds the Step Function for configured pipeline"""

        all_statemachines = []
        paginiator = self.client.get_paginator('list_state_machines')
        for page in paginiator.paginate():
            all_statemachines.extend(page['stateMachines'])

        for statemachine in all_statemachines:
            if statemachine['name'] == self.stepfunction_data.get('name', self.app_name):
                self.state_machine_arn = statemachine['stateMachineArn']
                LOG.info("Step Function State Machine Found")
                return True
        LOG.info("Step Function State Machine Not Found for %s", self.app_name)
        return False
