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
from ..utils import check_task, get_properties, get_subnets, get_template, get_vpc_id, post_task
from .format_listeners import format_listeners
from .splay_health import splay_health

log = logging.getLogger(__name__)


class SpinnakerELB:
    """Create ELBs for Spinnaker.

    Args:
        app (str): Application name.
        env (str): Deployment environment.
        prop_path (str): Path to the raw.properties.json.
        region (str): AWS Region.
    """

    def __init__(self, app='', env='', region='', prop_path=''):
        self.app = app
        self.env = env
        self.region = region
        self.properties = get_properties(properties_file=prop_path, env=self.env)

    def make_elb_json(self):
        """Render the JSON template with arguments.

        Returns:
            str: Rendered ELB template.
        """
        env = self.env
        region = self.region
        elb_settings = self.properties['elb']
        health_settings = elb_settings['health']
        elb_subnet_purpose = elb_settings.get('subnet_purpose', 'internal')

        region_subnets = get_subnets(target='elb', purpose=elb_subnet_purpose, env=env, region=region)
        region_subnets.pop("subnet_ids", None)

        # CAVEAT: Setting the ELB to public, you must use a public subnet,
        #         otherwise AWS complains about missing IGW on subnet.

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

        rendered_template = get_template(template_file='infrastructure/elb_data.json.j2', **template_kwargs)

        return rendered_template

    def create_elb(self):
        """Create or Update the ELB after rendering JSON data from configs.
        Asserts that the ELB task was successful.
        """

        json_data = self.make_elb_json()

        taskid = post_task(json_data)
        check_task(taskid)

        self.add_listener_policy(json_data)
        self.add_backend_policy(json_data)

    def add_listener_policy(self, json_data):
        """Attaches listerner policies to an ELB

        Args:
            json_data (json): return data from ELB upsert
        """
        env = boto3.session.Session(profile_name=self.env, region_name=self.region)
        elbclient = env.client('elb')

        #create stickiness policy if set in configs
        stickiness = {}
        elb_settings = self.properties['elb']
        if elb_settings.get('ports'):
            ports = elb_settings['ports']
            for listener in ports:
                if listener.get("stickiness"):
                    stickiness = self.add_stickiness()
                    log.info("Stickiness Found: %s", stickiness)
                    break

        #Attach policies to created ELB
        for job in json.loads(json_data)['job']:
            for listener in job['listeners']:
                policies = []
                ext_port = listener['externalPort']
                if listener['listenerPolicies']:
                    policies.extend(listener['listenerPolicies'])
                if stickiness.get(ext_port):
                    policies.append(stickiness.get(ext_port))
                if policies:
                    log.info("Adding listener policies: %s", policies)
                    elbclient.set_load_balancer_policies_of_listener(LoadBalancerName=self.app,
                                                                     LoadBalancerPort=ext_port,
                                                                     PolicyNames=policies)


    def add_backend_policy(self, json_data):
        """Attaches backend server policies to an ELB

        Args:
            json_data (json): return data from ELB upsert
        """
        env = boto3.session.Session(profile_name=self.env, region_name=self.region)
        elbclient = env.client('elb')

        # Attach backend server policies to created ELB
        for job in json.loads(json_data)['job']:
            for listener in job['listeners']:
                instance_port = listener['internalPort']
                backend_policy_list = listener['backendPolicies']
                if backend_policy_list:
                    log.info("Adding backend server policies: %s", backend_policy_list)
                    elbclient.set_load_balancer_policies_for_backend_server(LoadBalancerName=self.app,
                                                                            InstancePort=instance_port,
                                                                            PolicyNames=backend_policy_list)


    def add_stickiness(self):
        """ Adds stickiness policy to created ELB

        Returns:
            dict: A dict of stickiness policies and ports
                example:
                {
                    80: "$policy_name"
                }
        """
        stickiness_dict = {}
        env = boto3.session.Session(profile_name=self.env, region_name=self.region)
        elbclient = env.client('elb')
        elb_settings = self.properties['elb']
        for listener in elb_settings.get('ports'):
            if listener.get("stickiness"):
                sticky_type = listener['stickiness']['type'].lower()
                externalport = int(listener['loadbalancer'].split(":")[-1])
                policyname_tmp = "{0}-{1}-{2}-{3}"
                if sticky_type == 'app':
                    cookiename = listener['stickiness']['cookie_name']
                    policyname = policyname_tmp.format(self.app, sticky_type, externalport, cookiename)
                    elbclient.create_app_cookie_stickiness_policy(LoadBalancerName=self.app,
                                                                  PolicyName=policyname,
                                                                  CookieName=cookiename)
                    stickiness_dict[externalport] = policyname
                elif sticky_type == 'elb':
                    cookie_ttl = listener['stickiness'].get('cookie_ttl', None)
                    policyname = policyname_tmp.format(self.app, sticky_type, externalport, cookie_ttl)
                    if cookie_ttl:
                        elbclient.create_lb_cookie_stickiness_policy(LoadBalancerName=self.app,
                                                                     PolicyName=policyname,
                                                                     CookieExpirationPeriod=cookie_ttl)
                    else:
                        elbclient.create_lb_cookie_stickiness_policy(LoadBalancerName=self.app,
                                                                     PolicyName=policyname)
                    stickiness_dict[externalport] = policyname
        return stickiness_dict
