"""Create Security Groups for Spinnaker Pipelines."""
import ipaddress
import logging

import boto3
from boto3.exceptions import botocore
import requests

from ..consts import API_URL, HEADERS
from ..exceptions import (SpinnakerSecurityGroupCreationFailed,
                          SpinnakerTaskError, SpinnakerSecurityGroupError)
from ..utils import (check_task, get_template, get_vpc_id, get_properties,
                     get_security_group_id)


class SpinnakerSecurityGroup(object):
    """Manipulate Spinnaker Security Groups.

    Args:
        app_name: Str of application name add Security Group to.
    """

    def __init__(self, args):
        self.log = logging.getLogger(__name__)
        self.args = args

        self.app_name = self.args.app

        self.properties = get_properties(properties_file=self.args.properties,
                                         env=self.args.env)

    @staticmethod
    def _validate_cidr(rule):
        """Validate the cidr block in a rule.

        Returns:
            True: Upon successful completion.

        Raises:
            SpinnakerSecurityGroupCreationFailed: CIDR definition is invalid or
                the network range is too wide.
        """
        try:
            network = ipaddress.IPv4Network(rule['app'])
        except (ipaddress.NetmaskValueError, ValueError) as error:
            raise SpinnakerSecurityGroupCreationFailed(error)

        if network.prefixlen < 13:
            msg = 'The network range ({}) specified is too open.'.format(rule[
                'app'])
            raise SpinnakerSecurityGroupCreationFailed(msg)

        return True

    def _process_rules(self, rules):
        """Process rules into cidr and non-cidr lists.

        Args:
            rules (list): Allowed Security Group ports and protocols.

        Returns:
            (list, list): Security Group reference rules and custom CIDR rules.
        """
        cidr = []
        non_cidr = []

        for rule in rules:
            if '.' in rule['app']:
                self.log.debug('Custom CIDR rule: %s', rule)
                self._validate_cidr(rule)
                cidr.append(rule)
            else:
                self.log.debug('SG reference rule: %s', rule)
                non_cidr.append(rule)

        self.log.debug('Custom CIDR rules: %s', cidr)
        self.log.debug('SG reference rules: %s', non_cidr)
        return non_cidr, cidr

    def add_cidr_rules(self, rules):
        """Add cidr rules to security group via boto.

        Returns:
            True: Upon successful completion.

        Raises:
            SpinnakerSecurityGroupError: boto3 call failed to add CIDR block to
                Security Group.
        """
        session = boto3.session.Session(profile_name=self.args.env)
        client = session.client('ec2')

        group_id = get_security_group_id(self.app_name, self.args.env,
                                         self.args.region)

        for rule in rules:
            data = {
                'DryRun': False,
                'GroupId': group_id,
                'IpPermissions': [
                    {
                        'IpProtocol': rule['protocol'],
                        'FromPort': rule['start_port'],
                        'ToPort': rule['end_port'],
                        'IpRanges': [
                            {
                                'CidrIp': rule['app']
                            }
                        ]
                    }
                ]
            }
            self.log.debug('Security Group rule: %s', data)

            try:
                client.authorize_security_group_ingress(**data)
            except botocore.exceptions.ClientError as error:
                if 'InvalidPermission.Duplicate' in error:
                    self.log.debug('Duplicate rule exist, that is OK.')
                else:
                    msg = 'Unable to add cidr rules to {}'.format(rules['app'])
                    self.log.error(msg)
                    raise SpinnakerSecurityGroupError(msg)

        return True

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

        ingress_rules_no_cidr, ingress_rules_cidr = self._process_rules(
            ingress_rules)

        template_kwargs = {
            'app': self.args.app,
            'env': self.args.env,
            'region': self.args.region,
            'vpc': get_vpc_id(self.args.env, self.args.region),
            'description': self.properties['security_group']['description'],
            'ingress': ingress_rules_no_cidr,
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

        # Append cidr rules
        self.add_cidr_rules(ingress_rules_cidr)

        self.log.info('Successfully created %s security group', self.app_name)
        return True
