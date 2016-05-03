"""Create ELBs for Spinnaker Pipelines."""
import collections
import json
import logging

import requests

from ..consts import API_URL, HEADERS
from ..utils import check_task, get_subnets, get_template, get_vpc_id


class SpinnakerELB:
    """Create ELBs for Spinnaker."""

    log = logging.getLogger(__name__)

    def __init__(self, args=None):
        self.args = args
        self.properties = self.get_properties(
            properties_file=self.args.properties,
            env=self.args.env)

    @staticmethod
    def get_properties(properties_file='', env=''):
        """Get contents of _properties_file_ for the _env_."""
        with open(properties_file, 'rt') as file_handle:
            properties = json.load(file_handle)
        return properties[env]

    @staticmethod
    def splay_health(health_target):
        """Set Health Check path, port, and protocol.

        Returns:
            HealthCheck: A **collections.namedtuple** class with *path*, *port*,
            *proto*, and *target* attributes.
        """
        log = logging.getLogger(__name__)

        HealthCheck = collections.namedtuple('HealthCheck',
                                             ['path', 'port', 'proto',
                                              'target'])

        proto, health_port_path = health_target.split(':')
        port, *health_path = health_port_path.split('/')

        if proto == 'TCP':
            path = ''
        elif not health_path:
            path = '/healthcheck'
        else:
            path = '/{0}'.format('/'.join(health_path))

        target = '{0}:{1}{2}'.format(proto, port, path)

        health = HealthCheck(path, port, proto, target)
        log.info(health)

        return health

    def make_elb_json(self):
        """Render the JSON template with arguments.

        Returns:
            str: Rendered ELB template.
        """
        env = self.args.env
        region = self.args.region

        region_subnets = get_subnets(target='elb', env=env, region=region)

        elb_facing = 'true' if self.args.subnet_type == 'internal' else 'false'

        health = self.splay_health(self.args.health_target)

        template_kwargs = {
            'app_name': self.args.app,
            'availability_zones': json.dumps(region_subnets),
            'env': env,
            'ext_listener_port': self.args.ext_listener_port,
            'ext_listener_protocol': self.args.ext_listener_protocol,
            'hc_string': health.target,
            'health_interval': self.args.health_interval,
            'health_path': health.path,
            'health_port': health.port,
            'health_protocol': health.proto,
            'health_timeout': self.args.health_timeout,
            'healthy_threshold': self.args.healthy_threshold,
            'int_listener_port': self.args.int_listener_port,
            'int_listener_protocol': self.args.int_listener_protocol,
            'isInternal': elb_facing,
            'region_zones': json.dumps(region_subnets[region]),
            'region': region,
            'security_groups': json.dumps([self.args.security_groups]),
            'subnet_type': self.args.subnet_type,
            'unhealthy_threshold': self.args.unhealthy_threshold,
            'vpc_id': get_vpc_id(env, region),
        }

        rendered_template = get_template(
            template_file='elb_data_template.json',
            **template_kwargs)
        return rendered_template

    def create_elb(self):
        """Create/Update ELB.

        Args:
            json_data: elb json payload.
            app: application name related to this ELB.

        Returns:
            task id to track the elb creation status.
        """
        app = self.args.app
        json_data = self.make_elb_json()

        url = API_URL + '/applications/%s/tasks' % app
        response = requests.post(url, data=json_data, headers=HEADERS)

        assert response.ok, 'Error creating {0} ELB: {1}'.format(app,
                                                                 response.text)

        taskid = response.json()
        assert check_task(taskid, app)
