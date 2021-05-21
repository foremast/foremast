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
from contextlib import suppress

import boto3
from boto3.exceptions import botocore
from deepmerge import conservative_merger

from ..consts import DEFAULT_SECURITYGROUP_RULES
from ..exceptions import (ForemastConfigurationFileError, SpinnakerSecurityGroupCreationFailed,
                          SpinnakerSecurityGroupError)
from ..utils import get_details, get_properties, get_security_group_id, get_template, get_vpc_id, wait_for_task


class SpinnakerSecurityGroup:
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

        self.properties = get_properties(properties_file=prop_path, env=self.env, region=self.region)
        self.generated = get_details(app=self.app_name)
        self.group = self.generated.data['project']

    def _validate_cidr(self, rule):
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

        self.log.debug('Validating CIDR: %s', network.exploded)

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

    def add_tags(self):
        """Add tags to security group.

        Returns:
            True: Upon successful completion.
        """
        session = boto3.session.Session(profile_name=self.env, region_name=self.region)
        resource = session.resource('ec2')
        group_id = get_security_group_id(self.app_name, self.env, self.region)
        security_group = resource.SecurityGroup(group_id)

        try:
            tag = security_group.create_tags(
                DryRun=False,
                Tags=[{
                    'Key': 'app_group',
                    'Value': self.group
                }, {
                    'Key': 'app_name',
                    'Value': self.app_name
                }])
            self.log.debug('Security group has been tagged: %s', tag)
        except botocore.exceptions.ClientError as error:
            self.log.warning(error)

        return True

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
        session = boto3.session.Session(profile_name=self.env, region_name=self.region)
        client = session.client('ec2')

        group_id = get_security_group_id(self.app_name, self.env, self.region)

        for rule in rules:
            data = {
                'DryRun':
                False,
                'GroupId':
                group_id,
                'IpPermissions': [{
                    'IpProtocol': rule['protocol'],
                    'FromPort': rule['start_port'],
                    'ToPort': rule['end_port'],
                    'IpRanges': [{
                        'CidrIp': rule['app']
                    }]
                }]
            }
            self.log.debug('Security Group rule: %s', data)

            try:
                client.authorize_security_group_ingress(**data)
            except botocore.exceptions.ClientError as error:
                if 'InvalidPermission.Duplicate' in str(error):
                    self.log.debug('Duplicate rule exist, that is OK.')
                else:
                    msg = 'Unable to add cidr rules to {}'.format(rule.get('app'))
                    self.log.error(msg)
                    raise SpinnakerSecurityGroupError(msg)

        return True

    def resolve_self_references(self, rules):
        """Resolves `$self` references to actual application name in security group rules."""
        with suppress(KeyError):
            rule = rules.pop('$self')
            rules[self.app_name] = rule
        return rules

    def update_default_rules(self):
        """Concatinate application and global security group rules."""
        app_ingress = self.properties['security_group']['ingress']
        ingress = conservative_merger.merge(DEFAULT_SECURITYGROUP_RULES, app_ingress)
        resolved_ingress = self.resolve_self_references(ingress)
        self.log.info('Updated default rules:\n%s', ingress)
        return resolved_ingress

    def _create_security_group(self, ingress):
        """Send a POST to spinnaker to create a new security group.

        Returns:
            boolean: True if created successfully

        """
        template_kwargs = {
            'app': self.app_name,
            'env': self.env,
            'region': self.region,
            'vpc': get_vpc_id(self.env, self.region),
            'description': self.properties['security_group']['description'],
            'ingress': ingress,
        }

        secgroup_json = get_template(
            template_file='infrastructure/securitygroup_data.json.j2', formats=self.generated, **template_kwargs)

        wait_for_task(secgroup_json)
        return True

    def create_security_group(self):  # noqa
        """Send a POST to spinnaker to create or update a security group.

        Returns:
            boolean: True if created successfully

        Raises:
            ForemastConfigurationFileError: Missing environment configuration or
                misconfigured Security Group definition.
        """
        ingress_rules = []

        try:
            security_id = get_security_group_id(name=self.app_name, env=self.env, region=self.region)
        except (SpinnakerSecurityGroupError, AssertionError):
            self._create_security_group(ingress_rules)
        else:
            self.log.debug('Security Group ID %s found for %s.', security_id, self.app_name)

        try:
            ingress = self.update_default_rules()
        except KeyError:
            msg = 'Possible missing configuration for "{0}".'.format(self.env)
            self.log.error(msg)
            raise ForemastConfigurationFileError(msg)

        for app in ingress:
            rules = ingress[app]

            # Essentially we have two formats: simple, advanced
            # - simple: is just a list of ports
            # - advanced: selects ports ranges and protocols
            for rule in rules:
                ingress_rule = self.create_ingress_rule(app, rule)
                ingress_rules.append(ingress_rule)

        ingress_rules_no_cidr, ingress_rules_cidr = self._process_rules(ingress_rules)

        self._create_security_group(ingress_rules_no_cidr)

        # Append cidr rules
        self.add_cidr_rules(ingress_rules_cidr)

        # Tag security group
        self.add_tags()

        self.log.info('Successfully created %s security group', self.app_name)
        return True

    def create_ingress_rule(self, app, rule):
        """Create a normalized ingress rule.

        Args:
            app (str): Application name
            rule (dict or int): Allowed Security Group ports and protocols.

        Returns:
            dict: Contains app, start_port, end_port, protocol, cross_account_env and cross_account_vpc_id

        """
        if isinstance(rule, dict):
            # Advanced
            start_port = rule.get('start_port')
            end_port = rule.get('end_port')
            protocol = rule.get('protocol', 'tcp')

            requested_cross_account = rule.get('env', self.env)
            if self.env == requested_cross_account:
                # We are trying to use cross-account security group settings within the same account
                # We should not allow this.
                cross_account_env = None
                cross_account_vpc_id = None
            else:
                cross_account_env = requested_cross_account
                cross_account_vpc_id = get_vpc_id(cross_account_env, self.region)

        else:
            start_port = rule
            end_port = rule
            protocol = 'tcp'
            cross_account_env = None
            cross_account_vpc_id = None

        created_rule = {
            'app': app,
            'start_port': start_port,
            'end_port': end_port,
            'protocol': protocol,
            'cross_account_env': cross_account_env,
            'cross_account_vpc_id': cross_account_vpc_id
        }
        self.log.debug('Normalized ingress rule: %s', created_rule)
        return created_rule
