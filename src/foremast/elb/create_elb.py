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

"""Create ELBs for Spinnaker Pipelines."""
import json
import logging

import boto3

from ..consts import DEFAULT_ELB_SECURITYGROUPS
from ..utils import (check_task, get_properties, get_subnets, get_template,
                     get_vpc_id, post_task)
from .format_listeners import format_listeners
from .splay_health import splay_health


class SpinnakerELB:
    """Create ELBs for Spinnaker.

    Args:
        app (str): Application name.
        env (str): Deployment environment.
        prop_path (str): Path to the raw.properties.json.
        region (str): AWS Region.
    """

    log = logging.getLogger(__name__)

    def __init__(self, app='', env='', region='', prop_path=''):
        self.app = app
        self.env = env
        self.region = region
        self.properties = get_properties(properties_file=prop_path,
                                         env=self.env)

    def make_elb_json(self):
        """Render the JSON template with arguments.

        Returns:
            str: Rendered ELB template.
        """
        env = self.env
        region = self.region
        elb_settings = self.properties['elb']
        health_settings = elb_settings['health']

        region_subnets = get_subnets(target='elb', env=env, region=region)
        region_subnets.pop("subnet_ids", None)

        # CAVEAT: Setting the ELB to public, you must use a public subnet,
        #         otherwise AWS complains about missing IGW on subnet.

        elb_subnet_purpose = elb_settings.get('subnet_purpose', 'internal')

        if elb_subnet_purpose == 'internal':
            is_internal = 'true'
        else:
            is_internal = 'false'

        target = elb_settings.get('target', 'HTTP:80/health')
        health = splay_health(target)

        listeners = format_listeners(elb_settings=elb_settings, env=self.env)

        security_groups = list(DEFAULT_ELB_SECURITYGROUPS)
        security_groups.append(self.app)
        security_groups.extend(self.properties['security_group']['elb_extras'])

        template_kwargs = {
            'app_name': self.app,
            'availability_zones': json.dumps(region_subnets),
            'env': env,
            'hc_string': target,
            'health_interval': health_settings['interval'],
            'health_path': health.path,
            'health_port': health.port,
            'health_protocol': health.proto,
            'health_timeout': health_settings['timeout'],
            'healthy_threshold': health_settings['threshold'],
            'isInternal': is_internal,
            'listeners': json.dumps(listeners),
            'region_zones': json.dumps(region_subnets[region]),
            'region': region,
            'security_groups': json.dumps(security_groups),
            'subnet_type': elb_subnet_purpose,
            'unhealthy_threshold': health_settings['unhealthy_threshold'],
            'vpc_id': get_vpc_id(env, region),
        }

        rendered_template = get_template(
            template_file='infrastructure/elb_data.json.j2',
            **template_kwargs)

        return rendered_template

    def create_elb(self):
        """Create or Update the ELB after rendering JSON data from configs.
        Asserts that the ELB task was successful.
        """
        json_data = self.make_elb_json()

        taskid = post_task(json_data)
        check_task(taskid)

        self.add_listener_policy(json_data)

    def add_listener_policy(self, json_data):
        env = boto3.session.Session(profile_name=self.env, region_name=self.region)
        elbclient = env.client('elb')

        for job in json.loads(json_data)['job']:
            for listener in job['listeners']:
                if listener['listenerPolicies']:
                    elbclient.set_load_balancer_policies_of_listener(
                        LoadBalancerName=self.app,
                        LoadBalancerPort=listener['externalPort'],
                        PolicyNames=listener['listenerPolicies'])
