"""Create ELBs for Spinnaker Pipelines."""
import json
import logging
import os

import requests
from jinja2 import Environment, FileSystemLoader

LOG = logging.getLogger(__name__)


class SpinnakerELB:
    """Create ELBs for Spinnaker."""

    def __init__(self, args=None):
        self.args = args

        self.health_path = ''
        self.health_port = ''
        self.health_proto = ''
        self.set_health()

        self.here = os.path.dirname(os.path.realpath(__file__))
        self.templatedir = '{0}/../templates/'.format(self.here)
        jinjaenv = Environment(loader=FileSystemLoader(self.templatedir))
        self.elb_template = jinjaenv.get_template("elb_data_template.json")
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

    def create_elb(self, json_data, app):
        """Create/Update ELB.

        Args:
            json_data: elb json payload.
            app: application name related to this ELB.

        Returns:
            task id to track the elb creation status.
        """
        url = self.gate_url + '/applications/%s/tasks' % app
        response = requests.post(url,
                                 data=json.dumps(json_data),
                                 headers=self.header)
        if response.ok:
            LOG.info('%s ELB Created', app)
            LOG.info(response.text)
            return response.json()
        else:
            LOG.error('Error creating %s ELB:', app)
            LOG.error(response.text)
            return response.json()
