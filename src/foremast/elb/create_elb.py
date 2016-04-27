"""Create ELBs for Spinnaker Pipelines."""
import argparse
import json
import logging
import os

import requests
from jinja2 import Environment, FileSystemLoader

from .utils import check_task, get_subnets, get_vpc_id

LOG = logging.getLogger(__name__)


class SpinnakerELB:
    """Create ELBs for Spinnaker."""

    def __init__(self):
        self.curdir = os.path.dirname(os.path.realpath(__file__))
        self.templatedir = "{}/../../templates".format(self.curdir)
        jinjaenv = Environment(loader=FileSystemLoader(self.templatedir))
        self.elb_template = jinjaenv.get_template("elb_data_template.json")
        self.gate_url = "http://gate-api.build.example.com:8084"
        self.header = {'Content-Type': 'application/json', 'Accept': '*/*'}

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
