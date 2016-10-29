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

"""Create Security Groups for Spinnaker Pipelines.

Security Group port specifications will be sourced from the `application.json`
files for each environment.

Examples:
    application-master.json::

        {
            "security_group": {
                "description": "Security Group description",
                "ingress": {
                    "eureka": [
                        {"start_port": 80, "end_port": 8080, "protocol": "tcp"}
                    ],
                    "coreforrest": [
                        8080,
                        8443
                    ],
                    "0.0.0.0/0": [
                        8080
                    ]
                }
            }
        }
"""
import ipaddress
import logging

import boto3
from boto3.exceptions import botocore

from ..exceptions import (ForemastConfigurationFileError, SpinnakerSecurityGroupCreationFailed,
                          SpinnakerSecurityGroupError)
from ..utils import check_task, get_properties, get_security_group_id, get_template, get_vpc_id, post_task, warn_user


class SpinnakerSecurityGroup(object):
    """Manipulate Spinnaker Security Groups.

    Args:
        app (str): Application name.
        env (str): Deployment environment.
        prop_path (str): Path to the raw.properties.json.
        region (str): AWS Region.
    """

    def __init__(self, app=None, env=None, region=None, prop_path=None):
        self.log = logging.getLogger(__name__)

        self.app_name = app
        self.env = env
        self.region = region

        self.properties = get_properties(properties_file=prop_path, env=env)

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
            msg = 'The network range ({0}) specified is too open.'.format(rule[
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

        Args:
            rules (list): Allowed Security Group ports and protocols.

        Returns:
            True: Upon successful completion.

        Raises:
            SpinnakerSecurityGroupError: boto3 call failed to add CIDR block to
                Security Group.
        """
        session = boto3.session.Session(profile_name=self.env,
                                        region_name=self.region)
        client = session.client('ec2')

        group_id = get_security_group_id(self.app_name, self.env, self.region)

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
                if 'InvalidPermission.Duplicate' in str(error):
                    self.log.debug('Duplicate rule exist, that is OK.')
                else:
                    msg = 'Unable to add cidr rules to {}'.format(rules['app'])
                    self.log.error(msg)
                    raise SpinnakerSecurityGroupError(msg)

        return True

    def create_security_group(self):
        """Send a POST to spinnaker to create a new security group.

        Returns:
            boolean: True if created successfully

        Raises:
            ForemastConfigurationFileError: Missing environment configuration or
                misconfigured Security Group definition.
        """
        ingress_rules = []

        try:
            ingress = self.properties['security_group']['ingress']
        except KeyError:
            msg = 'Possible missing configuration for "{0}".'.format(self.env)
            self.log.error(msg)
            raise ForemastConfigurationFileError(msg)

        for app in ingress:
            rules = ingress[app]

            if app in ('app_a', 'app_b'):
                msg = (
                    'Using "{0}" in your security group will be ignored. '
                    'Please remove them to suppress this warning.').format(app)
                warn_user(msg)
                continue

            # Essentially we have two formats: simple, advanced
            # - simple: is just a list of ports
            # - advanced: selects ports ranges and protocols
            for rule in rules:
                try:
                    # Advanced
                    start_port = rule.get('start_port')
                    end_port = rule.get('end_port')
                    protocol = rule.get('protocol', 'tcp')
                    cross_account_env = rule.get('env', None)
                    cross_account_vpc_id = None
                except AttributeError:
                    start_port = rule
                    end_port = rule
                    protocol = 'tcp'
                    cross_account_env = None
                    cross_account_vpc_id = None

                if cross_account_env:
                    cross_account_vpc_id = get_vpc_id(cross_account_env,
                                                      self.region)

                ingress_rules.append({
                    'app': app,
                    'start_port': start_port,
                    'end_port': end_port,
                    'protocol': protocol,
                    'cross_account_env': cross_account_env,
                    'cross_account_vpc_id': cross_account_vpc_id
                })

        ingress_rules_no_cidr, ingress_rules_cidr = self._process_rules(
            ingress_rules)

        template_kwargs = {
            'app': self.app_name,
            'env': self.env,
            'region': self.region,
            'vpc': get_vpc_id(self.env, self.region),
            'description': self.properties['security_group']['description'],
            'ingress': ingress_rules_no_cidr,
        }

        secgroup_json = get_template(
            template_file='infrastructure/securitygroup_data.json.j2',
            **template_kwargs)

        taskid = post_task(secgroup_json)
        check_task(taskid)

        # Append cidr rules
        self.add_cidr_rules(ingress_rules_cidr)

        self.log.info('Successfully created %s security group', self.app_name)
        return True
