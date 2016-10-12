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

"""Manages AWS scaling policies in Spinnaker. Can find, create, and delete.

This module also creates an inverse policy for scaling down
"""
import json
import logging
import os

import requests

from ..consts import API_URL, GATE_CA_BUNDLE, GATE_CLIENT_CERT
from ..utils import check_task, get_properties, get_template, post_task


class AutoScalingPolicy:
    """Manages scaling policies in Spinnaker

    Args:
        app (str): Application name
        prop_path (str): Path of rendered property files
        env (str): Environment/Account to add policy to
        region (str): AWS region for policy

    Attributes:
        log (str): Logger name
        settings (dict): Properties imported from prop_path
    """

    def __init__(self, app='', prop_path='', env='', region=''):

        self.log = logging.getLogger(__name__)

        self.here = os.path.dirname(os.path.realpath(__file__))
        self.env = env
        self.region = region
        self.app = app

        self.settings = get_properties(properties_file=prop_path, env=self.env)

    def prepare_policy_template(self, scaling_type, period_sec, server_group):
        """Renders scaling policy templates based on configs and variables.
        After rendering, POSTs the json to Spinnaker for creation.

        Args:
            scaling_type (str): ``scale_up`` or ``scaling_down``. Type of policy
            period_sec (int): Period of time to look at metrics for determining scale
            server_group (str): The name of the server group to render template for
        """
        template_kwargs = {}
        if scaling_type == 'scale_up':
            template_kwargs = {
                'app': self.app,
                'env': self.env,
                'region': self.region,
                'server_group': server_group,
                'period_sec': period_sec,
                'scaling_policy': self.settings['asg']['scaling_policy'],
                'operation': 'increase',
                'comparisonOperator': 'GreaterThanThreshold',
                'scalingAdjustment': 1
            }
        elif scaling_type == 'scale_down':
            self.settings['asg']['scaling_policy']['threshold'] = self.settings[
                'asg']['scaling_policy']['threshold'] * 0.5
            template_kwargs = {
                'app': self.app,
                'env': self.env,
                'region': self.region,
                'server_group': server_group,
                'period_sec': period_sec,
                'scaling_policy': self.settings['asg']['scaling_policy'],
                'operation': 'decrease',
                'comparisonOperator': 'LessThanThreshold',
                'scalingAdjustment': -1
            }

        self.log.info('Rendering Scaling Policy Template: {0}'.format(
            template_kwargs))
        rendered_template = get_template(
            template_file='infrastructure/autoscaling_policy.json.j2',
            **template_kwargs)
        print(rendered_template)
        taskid = post_task(rendered_template)
        check_task(taskid)
        self.log.info('Successfully created scaling policy in {0}'.format(
            self.env))

    def create_policy(self):
        """Wrapper function. Gets the server group, sets sane defaults,
        deletes existing policies, and then runs self.prepare_policy_template
        for scaling up and scaling down policies.
        This function acts as the main driver for the scaling policy creationprocess
        """
        if not self.settings['asg']['scaling_policy']:
            self.log.info("No scaling policy found, skipping...")
            return

        server_group = self.get_server_group()

        # Find all existing and remove them
        scaling_policies = self.get_all_existing()
        for policy in scaling_policies:
            for subpolicy in policy:
                self.delete_existing_policy(subpolicy, server_group)

        if self.settings['asg']['scaling_policy']['period_minutes']:
            period_sec = self.settings['asg']['scaling_policy']['period_minutes'] * 60
        else:
            period_sec = 1800
        self.prepare_policy_template('scale_up', period_sec, server_group)
        self.prepare_policy_template('scale_down', period_sec, server_group)

    def get_server_group(self):
        """Finds the most recently deployed server group for the application.
        This is the server group that the scaling policy will be applied to.

        Returns:
            server_group (str): Name of the newest server group
        """
        api_url = "{0}/applications/{1}".format(API_URL, self.app)
        response = requests.get(api_url,
                                verify=GATE_CA_BUNDLE,
                                cert=GATE_CLIENT_CERT)
        for server_group in response.json()['clusters'][self.env]:
            return server_group['serverGroups'][-1]

    def delete_existing_policy(self, scaling_policy, server_group):
        """Given a scaling_policy and server_group, deletes the existing scaling_policy.
        Scaling policies need to be deleted instead of upserted for consistency.

        Args:
            scaling_policy (json): the scaling_policy json from Spinnaker that should be deleted
            server_group (str): the affected server_group
        """
        self.log.info("Deleting policy {}".format(scaling_policy['policyName']))
        delete_dict = {
            "application": self.app,
            "description": "Delete scaling policy",
            "job": [
                {
                    "policyName": scaling_policy['policyName'],
                    "serverGroupName": server_group,
                    "credentials": self.env,
                    "region": self.region,
                    "provider": "aws",
                    "type": "deleteScalingPolicy",
                    "user": "pipes-autoscaling-policy"
                }]}
        taskid = post_task(json.dumps(delete_dict))
        check_task(taskid)

    def get_all_existing(self):
        """Finds all existing scaling policies for an application

        Returns:
            scalingpolicies (list): List of all existing scaling policies for the application
        """
        self.log.info("Checking for existing scaling policy")
        url = "{0}/applications/{1}/clusters/{2}/{1}/serverGroups".format(
            API_URL, self.app, self.env)
        response = requests.get(url,
                                verify=GATE_CA_BUNDLE,
                                cert=GATE_CLIENT_CERT)
        assert response.ok, "Error looking for existing Autoscaling Policy for {0}: {1}".format(
            self.app, response.text)

        scalingpolicies = []
        for servergroup in response.json():
            if servergroup['scalingPolicies']:
                scalingpolicies.append(servergroup['scalingPolicies'])
        return scalingpolicies
