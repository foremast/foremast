"""Create Security Groups for Spinnaker Pipelines."""
import logging
import os

import requests

from ..consts import API_URL, HEADERS
from ..exceptions import (SpinnakerSecurityGroupCreationFailed,
                          SpinnakerTaskError)
from ..utils import check_task, get_template, get_vpc_id


class SpinnakerSecurityGroup:
    """Manipulate Spinnaker Security Groups.

    Args:
        app_name: Str of application name add Security Group to.
    """

    def __init__(self, app_info):
        self.log = logging.getLogger(__name__)

        self.here = os.path.dirname(os.path.realpath(__file__))
        self.app_info = app_info
        self.app_name = app_info['app']

    def create_security_group(self):
        """Sends a POST to spinnaker to create a new security group."""
        url = "{0}/applications/{1}/tasks".format(API_URL, self.app_name)

        self.app_info['vpc'] = get_vpc_id(self.app_info['env'],
                                          self.app_info['region'])

        secgroup_json = get_template(
            template_file='securitygroup_template.json',
            **self.app_info)

        r = requests.post(url, data=secgroup_json, headers=HEADERS)

        assert r.ok, 'Failed to create Security Group for {0}: {1}'.format(
            self.app_name, r.text)

        try:
            check_task(r.json(), self.app_name)
        except SpinnakerTaskError as error:
            logging.error('Failed to create Security Group for %s: %s',
                          self.app_name, r.text)
            raise SpinnakerSecurityGroupCreationFailed(error)

        logging.info('Successfully created %s security group', self.app_name)
        return True
