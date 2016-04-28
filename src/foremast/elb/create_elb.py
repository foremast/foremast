"""Create ELBs for Spinnaker Pipelines."""
import json
import logging

import requests

from ..utils import check_task, get_subnets, get_template, get_vpc_id

LOG = logging.getLogger(__name__)


class SpinnakerELB:
    """Create ELBs for Spinnaker."""

    def __init__(self, args=None):
        self.args = args

        self.health_path = ''
        self.health_port = ''
        self.health_proto = ''
        self.set_health()

        self.gate_url = "http://gate-api.build.example.com:8084"
        self.header = {'Content-Type': 'application/json', 'Accept': '*/*'}

    def set_health(self):
        """Set Health Check path, port, and protocol."""
        target = self.args.health_target
        self.health_proto, health_port_path = target.split(':')
        self.health_port, *health_path = health_port_path.split('/')

        if not health_path:
            self.health_path = '/healthcheck'
        else:
            self.health_path = '/{0}'.format('/'.join(health_path))

        LOG.info('Health Check\n\tprotocol: %s\n\tport: %s\n\tpath: %s',
                 self.health_proto, self.health_port, self.health_path)

        return True

    def make_elb_json(self):
        """Render the JSON template with arguments.

        Returns:
            str: Rendered ELB template.
        """
        raw_subnets = get_subnets(target='elb')
        region_subnets = {self.args.region:
                          raw_subnets[self.args.env][self.args.region]}

        env = self.args.env
        region = self.args.region

        elb_facing = 'true' if self.args.subnet_type == 'internal' else 'false'

        kwargs = {
            'app_name': self.args.app,
            'env': env,
            'isInternal': elb_facing,
            'vpc_id': get_vpc_id(env, region),
            'health_protocol': self.health_proto,
            'health_path': self.health_path,
            'health_port': self.health_port,
            'health_timeout': self.args.health_timeout,
            'health_interval': self.args.health_interval,
            'unhealthy_threshold': self.args.unhealthy_threshold,
            'healthy_threshold': self.args.healthy_threshold,
            # FIXME: Use json.dumps(args.security_groups) to format for template
            'security_groups': self.args.security_groups,
            'int_listener_protocol': self.args.int_listener_protocol,
            'int_listener_port': self.args.int_listener_port,
            'ext_listener_port': self.args.ext_listener_port,
            'ext_listener_protocol': self.args.ext_listener_protocol,
            'subnet_type': self.args.subnet_type,
            'region': region,
            'hc_string': self.args.health_target,
            'availability_zones': json.dumps(region_subnets),
            'region_zones': json.dumps(region_subnets[region]),
        }

        rendered_template = get_template(
            template_file='elb_data_template.json',
            **kwargs)
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

        url = self.gate_url + '/applications/%s/tasks' % app
        response = requests.post(url, data=json_data, headers=self.header)

        assert response.ok, 'Error creating {0} ELB: {1}'.format(app,
                                                                 response.text)

        taskid = response.json()
        assert check_task(taskid, app)
