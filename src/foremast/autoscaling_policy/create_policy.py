import json
import logging

import requests

from ..consts import API_URL
from ..utils import (get_properties, get_template)


class AutoScalingPolicy:

    def __init__(self,
                 app_name='',
                 prop_path='',
                 env='',
                 region='')
        self.log = logging.getLogger(__name__)

        self.header = {'content-type': 'application/json'}
        self.here = os.path.dirname(os.path.realpath(__file__))
        self.env = env
        self.region = region
        self.app_name = app_name

        self.settings = get_properties(properties_file=prop_path, env=self.env)

    def create_policy(self):
        server_group = get_server_group(self.app_name, self.env)

        template_kwargs = {
            'app_name' = self.app_name,
            'env' = self.env,
            'region' = self.region,
            'server_group' = server_group,
            'scaling_policy' = self.settings['scaling_policy']
            }

        rendered_template = get_template(
                    template_file='scaling_policy_template.json',
                    **template_kwargs)

        self.post_task(rendered_template)


    def post_task(self,  payload):
        """Sends the POST to the correct endpoint and reports results"""
        url = "{0}/applications/{1}/tasks".format(API_URL, self.app_name)
        response = requests.post(url,
                                 data=payload,
                                 headers=self.headers)
        assert response.ok, "Error creating {0} Autoscaling Policy: {1}".format(self.app_name,
                                                                                response.text)


    def get_server_group(self):
        response = requests.get("{0}/applications/{1}".format(API_URL, self.app_name)
        for server_group in response.json['clusters'][self.env]:
            return server_group['serverGroups'][-1]


if __name__ == '__main__':
    policy = AutoScalingPolicy(app_name="edgeforrest",
                               prop_path="
