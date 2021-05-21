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
"""Create ELBs for Spinnaker Pipelines."""
import json
import logging
from pprint import pformat

import boto3

from ..consts import DEFAULT_ELB_SECURITYGROUPS
from ..utils import get_properties, get_subnets, get_template, get_vpc_id, remove_duplicate_sg, wait_for_task
from .format_listeners import format_listeners
from .splay_health import splay_health

LOG = logging.getLogger(__name__)


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
        self.properties = get_properties(properties_file=prop_path, env=self.env, region=self.region)

    def make_elb_json(self):
        """Render the JSON template with arguments.

        Returns:
            str: Rendered ELB template.
        """
        env = self.env
        region = self.region
        elb_settings = self.properties['elb']
        LOG.debug('Block ELB Settings:\n%s', pformat(elb_settings))

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

        listeners = format_listeners(elb_settings=elb_settings, env=self.env, region=region)

        idle_timeout = elb_settings.get('idle_timeout', None)
        access_log = elb_settings.get('access_log', {})
        connection_draining_timeout = elb_settings.get('connection_draining_timeout', None)

        security_groups = DEFAULT_ELB_SECURITYGROUPS[env]
        security_groups.append(self.app)
        security_groups.extend(self.properties['security_group']['elb_extras'])
        security_groups = remove_duplicate_sg(security_groups)

        template_kwargs = {
            'access_log': json.dumps(access_log),
            'app_name': self.app,
            'availability_zones': json.dumps(region_subnets),
            'connection_draining_timeout': json.dumps(connection_draining_timeout),
            'env': env,
            'hc_string': target,
            'health_interval': health_settings['interval'],
            'health_path': health.path,
            'health_port': health.port,
            'health_protocol': health.proto,
            'health_timeout': health_settings['timeout'],
            'healthy_threshold': health_settings['threshold'],
            'idle_timeout': json.dumps(idle_timeout),
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
        LOG.debug('Block ELB JSON Data:\n%s', pformat(json_data))

        wait_for_task(json_data)

        self.add_listener_policy(json_data)
        self.add_backend_policy(json_data)

        self.configure_attributes(json_data)

    def add_listener_policy(self, json_data):
        """Attaches listerner policies to an ELB

        Args:
            json_data (json): return data from ELB upsert
        """
        env = boto3.session.Session(profile_name=self.env, region_name=self.region)
        elbclient = env.client('elb')

        # create stickiness policy if set in configs
        stickiness = {}
        elb_settings = self.properties['elb']
        if elb_settings.get('ports'):
            ports = elb_settings['ports']
            for listener in ports:
                if listener.get("stickiness"):
                    stickiness = self.add_stickiness()
                    LOG.info('Stickiness Found: %s', stickiness)
                    break

        # Attach policies to created ELB
        for job in json.loads(json_data)['job']:
            for listener in job['listeners']:
                policies = []
                ext_port = listener['externalPort']
                if listener['listenerPolicies']:
                    policies.extend(listener['listenerPolicies'])
                if stickiness.get(ext_port):
                    policies.append(stickiness.get(ext_port))
                if policies:
                    LOG.info('Adding listener policies: %s', policies)
                    elbclient.set_load_balancer_policies_of_listener(
                        LoadBalancerName=self.app, LoadBalancerPort=ext_port, PolicyNames=policies)

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
                    LOG.info('Adding backend server policies: %s', backend_policy_list)
                    elbclient.set_load_balancer_policies_for_backend_server(
                        LoadBalancerName=self.app, InstancePort=instance_port, PolicyNames=backend_policy_list)

    def add_stickiness(self):
        """ Adds stickiness policy to created ELB

        Returns:
            dict: A dict of stickiness policies and ports::

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
                    policy_key = cookiename.replace('.', '')
                    policyname = policyname_tmp.format(self.app, sticky_type, externalport, policy_key)
                    elbclient.create_app_cookie_stickiness_policy(
                        LoadBalancerName=self.app, PolicyName=policyname, CookieName=cookiename)
                    stickiness_dict[externalport] = policyname
                elif sticky_type == 'elb':
                    cookie_ttl = listener['stickiness'].get('cookie_ttl', None)
                    policyname = policyname_tmp.format(self.app, sticky_type, externalport, cookie_ttl)
                    if cookie_ttl:
                        elbclient.create_lb_cookie_stickiness_policy(
                            LoadBalancerName=self.app, PolicyName=policyname, CookieExpirationPeriod=cookie_ttl)
                    else:
                        elbclient.create_lb_cookie_stickiness_policy(LoadBalancerName=self.app, PolicyName=policyname)
                    stickiness_dict[externalport] = policyname
        return stickiness_dict

    def configure_attributes(self, json_data):
        """Configure load balancer attributes such as idle timeout, connection draining, etc

        Args:
            json_data (json): return data from ELB upsert
        """
        env = boto3.session.Session(profile_name=self.env, region_name=self.region)
        elbclient = env.client('elb')

        elb_settings = self.properties['elb']
        LOG.debug('Block ELB Settings Pre Configure Load Balancer Attributes:\n%s', pformat(elb_settings))

        # FIXME: Determine why 'job' is not being used
        # pylint: disable=unused-variable
        for job in json.loads(json_data)['job']:
            load_balancer_attributes = {
                'CrossZoneLoadBalancing': {
                    'Enabled': True
                },
                'AccessLog': {
                    'Enabled': False,
                },
                'ConnectionDraining': {
                    'Enabled': False,
                },
                'ConnectionSettings': {
                    'IdleTimeout': 60
                }
            }
            if elb_settings.get('connection_draining_timeout'):
                connection_draining_timeout = int(elb_settings['connection_draining_timeout'])
                LOG.info('Applying Custom Load Balancer Connection Draining Timeout: %d', connection_draining_timeout)
                load_balancer_attributes['ConnectionDraining'] = {
                    'Enabled': True,
                    'Timeout': connection_draining_timeout
                }
            if elb_settings.get('idle_timeout'):
                idle_timeout = int(elb_settings['idle_timeout'])
                LOG.info('Applying Custom Load Balancer Idle Timeout: %d', idle_timeout)
                load_balancer_attributes['ConnectionSettings'] = {'IdleTimeout': idle_timeout}
            if elb_settings.get('access_log'):
                access_log_bucket_name = elb_settings['access_log']['bucket_name']
                access_log_bucket_prefix = elb_settings['access_log']['bucket_prefix']
                access_log_emit_interval = int(elb_settings['access_log']['emit_interval'])
                LOG.info('Applying Custom Load Balancer Access Log: %s/%s every %d minutes', access_log_bucket_name,
                         access_log_bucket_prefix, access_log_emit_interval)
                load_balancer_attributes['AccessLog'] = {
                    'Enabled': True,
                    'S3BucketName': access_log_bucket_name,
                    'EmitInterval': access_log_emit_interval,
                    'S3BucketPrefix': access_log_bucket_prefix
                }

            LOG.info('Applying Load Balancer Attributes')
            LOG.debug('Load Balancer Attributes:\n%s', pformat(load_balancer_attributes))
            elbclient.modify_load_balancer_attributes(
                LoadBalancerName=self.app, LoadBalancerAttributes=load_balancer_attributes)
