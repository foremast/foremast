import json
import logging
import os

import requests

from ..consts import API_URL
from ..utils import (get_properties, get_template)


class AutoScalingPolicy:
    """Creates scaling policies for Spinnaker

    Args:
        app: Str of the application name
        prop_path: Str of the path to property files
        env: Str of env to add policy
        region: Str of region for policy
    """

    def __init__(self,
                 app='',
                 prop_path='',
                 env='',
                 region='' ):

        self.log = logging.getLogger(__name__)

        self.header = {'content-type': 'application/json'}
        self.here = os.path.dirname(os.path.realpath(__file__))
        self.env = env
        self.region = region
        self.app = app

        self.settings = get_properties(properties_file=prop_path, env=self.env)


    def create_policy(self):
        """ Renders the template and creates the police """

        if not self.settings['asg']['scaling_policy']:
            self.log.info("No scaling policy found, skipping...")
            return

        server_group = self.get_server_group()

        template_kwargs = {
                'app': self.app,
                'env': self.env,
                'region': self.region,
                'server_group': server_group,
                'scaling_policy': self.settings['asg']['scaling_policy']
            }
        self.log.info('Rendering Scaling Policy Template')
        rendered_template = get_template(
                    template_file='scaling_policy_template.json',
                    **template_kwargs)

        self.post_task(rendered_template)
        self.log.info('Successfully created scaling policy in {0}'.format(self.env))


    def post_task(self,  payload):
        """ Posts the rendered template to correct endpoint """
        """Sends the POST to the correct endpoint and reports results"""
        url = "{0}/applications/{1}/tasks".format(API_URL, self.app)
        response = requests.post(url,
                                 data=payload,
                                 headers=self.headers)
        assert response.ok, "Error creating {0} Autoscaling Policy: {1}".format(self.app,
                                                                                response.text)

    def get_server_group(self):
        """ Gets the current server group """
        response = requests.get("{0}/applications/{1}".format(API_URL, self.app))
        print(response)
        for server_group in response.json()['clusters'][self.env]:
            return server_group['serverGroups'][-1]

