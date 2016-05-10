"""Create Security Groups for Spinnaker Pipelines."""
import logging

import requests

from ..consts import API_URL, HEADERS
from ..exceptions import (SpinnakerSecurityGroupCreationFailed,
                          SpinnakerTaskError)
from ..utils import check_task, get_template, get_vpc_id, get_properties


class SpinnakerSecurityGroup:
    """Manipulate Spinnaker Security Groups.

    Args:
        app_name: Str of application name add Security Group to.
    """

    def __init__(self, args):
        self.log = logging.getLogger(__name__)
        self.args = args

        self.app_name = self.args.app

        self.properties = get_properties(
            properties_file=self.args.properties,
            env=self.args.env)

    def create_security_group(self):
        """Send a POST to spinnaker to create a new security group."""
        url = "{0}/applications/{1}/tasks".format(API_URL, self.app_name)

        self.args.vpc = get_vpc_id(self.args.env, self.args.region)

        ingress = self.properties['security_group']['ingress']
        ingress_rules = []

        for app in ingress:
            rules = ingress[app]
            # Essentially we have two formats: simple, advanced
            # - simple: is just a list of ports
            # - advanced: selects ports ranges and protocols
            for rule in rules:
                try:
                    # Advanced
                    start_port = rule.get('start_port')
                    end_port = rule.get('end_port')
                    protocol = rule.get('protocol', 'tcp')
                except AttributeError:
                    start_port = rule
                    end_port = rule
                    protocol = 'tcp'

                ingress_rules.append({
                    'app': app,
                    'start_port': start_port,
                    'end_port': end_port,
                    'protocol': protocol,
                    })
        logging.debug(ingress_rules)

        template_kwargs = {
            'app': self.args.app,
            'env': self.args.env,
            'region': self.args.region,
            'vpc': get_vpc_id(self.args.env, self.args.region),
            'description': self.properties['security_group']['description'],
            'ingress': ingress_rules,
        }

        secgroup_json = get_template(
            template_file='securitygroup_template.json',
            **template_kwargs)

        response = requests.post(url, data=secgroup_json, headers=HEADERS)

        assert response.ok, ('Failed Security Group request for {0}: '
                             '{1}').format(self.app_name, response.text)

        try:
            check_task(response.json(), self.app_name)
        except SpinnakerTaskError as error:
            self.log.error('Failed to create Security Group for %s: %s',
                          self.app_name, response.text)
            raise SpinnakerSecurityGroupCreationFailed(error)

        self.log.info('Successfully created %s security group', self.app_name)
        return True
