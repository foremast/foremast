import json
import logging
import os

import requests

from ..consts import API_URL
from ..utils import (get_properties, get_template, check_task)


class AutoScalingPolicy:
    """Creates scaling policies for Spinnaker

    Args:
        app: Str of the application name
        prop_path: Str of the path to property files
        env: Str of env to add policy
        region: Str of region for policy
    """

    def __init__(self, app='', prop_path='', env='', region=''):

        self.log = logging.getLogger(__name__)

        self.header = {'content-type': 'application/json'}
        self.here = os.path.dirname(os.path.realpath(__file__))
        self.env = env
        self.region = region
        self.app = app

        self.settings = get_properties(properties_file=prop_path, env=self.env)

    def prepare_policy_template(self, scaling_type, period_sec, server_group):
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
            self.log.info('Rendering Scaling Policy Template: {0}'.format(
                template_kwargs))
            rendered_template = get_template(
                template_file='autoscaling_policy_template.json',
                **template_kwargs)

            self.post_task(rendered_template)
            self.log.info('Successfully created scaling policy in {0}'.format(
                self.env))
        elif scaling_type == 'scale_down':
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
                template_file='autoscaling_policy_template.json',
                **template_kwargs)

            self.post_task(rendered_template)
            self.log.info('Successfully created scaling policy in {0}'.format(
                self.env))

    def create_policy(self):
        """ Renders the template and creates the police """

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

    def post_task(self, payload):
        """ Posts the rendered template to correct endpoint """
        """Sends the POST to the correct endpoint and reports results"""
        url = "{0}/applications/{1}/tasks".format(API_URL, self.app)
        response = requests.post(url, data=payload, headers=self.header)
        assert response.ok, "Error creating {0} Autoscaling Policy: {1}".format(
            self.app, response.text)
        check_task(response.json()['ref'], self.app)

    def get_server_group(self):
        """ Gets the current server group """
        response = requests.get("{0}/applications/{1}".format(API_URL,
                                                              self.app))
        for server_group in response.json()['clusters'][self.env]:
            return server_group['serverGroups'][-1]

    def delete_existing_policy(self, scaling_policy, server_group):
        self.log.info("Deleting policy {}".format(scaling_policy['policyName']))
        delete_dict = {
            "application": self.app,
            "description": "Delete scaling policy",
            "job": [
                {
                    "policyName": scaling_policy['policyName'],
                    "serverGroupName": server_group,
                    "credentials":self.env,
                    "region":self.region,
                    "provider":"aws",
                    "type":"deleteScalingPolicy",
                    "user":"pipes-autoscaling-policy"
                }]}
        self.post_task(json.dumps(delete_dict))

    def get_all_existing(self):
        """ Returns list of all existing policies """
        self.log.info("Checking for existing scaling policy")
        url = "{0}/applications/{1}/clusters/{2}/{1}/serverGroups".format(
            API_URL, self.app, self.env)
        response = requests.get(url)
        assert response.ok, "Error looking for existing Autoscaling Policy for {0}: {1}".format(
            self.app, response.text)

        scalingpolicies = []
        for servergroup in response.json():
            if servergroup['scalingPolicies']:
                scalingpolicies.append(servergroup['scalingPolicies'])
        return scalingpolicies
