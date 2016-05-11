"""Create ELBs for Spinnaker Pipelines."""
import json
import logging

import requests

from ..consts import API_URL, HEADERS
from ..utils import check_task, get_subnets, get_template, get_vpc_id
from .format_listeners import format_listeners
from .splay_health import splay_health


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

    def make_elb_json(self):
        """Render the JSON template with arguments.

        Returns:
            str: Rendered ELB template.
        """
        env = self.args.env
        region = self.args.region
        elb_settings = self.properties['elb']

        region_subnets = get_subnets(target='elb', env=env, region=region)

        subnet_purpose = self.properties.get('subnet_purpose', 'internal')
        elb_facing = 'true' if subnet_purpose == 'internal' else 'false'

        target = elb_settings.get('target', 'HTTP:80/health')
        health = splay_health(target)

        listeners = format_listeners(elb_settings=elb_settings)

        security_groups = ['sg_apps', self.args.app] + self.properties['security_group']['elb_extras']

        template_kwargs = {
            'app_name': self.args.app,
            'availability_zones': json.dumps(region_subnets),
            'env': env,
            'hc_string': target,
            'health_interval': self.args.health_interval,
            'health_path': health.path,
            'health_port': health.port,
            'health_protocol': health.proto,
            'health_timeout': self.args.health_timeout,
            'healthy_threshold': self.args.healthy_threshold,
            'isInternal': elb_facing,
            'listeners': json.dumps(listeners),
            'region_zones': json.dumps(region_subnets[region]),
            'region': region,
            'security_groups': json.dumps(security_groups),
            'subnet_type': subnet_purpose,
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
