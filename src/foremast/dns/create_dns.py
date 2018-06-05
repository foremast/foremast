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
"""Module to create dynamically generated DNS record in route53"""
import logging

from ..consts import DOMAIN
from ..utils import (find_elb, find_elb_dns_zone_id, get_details, get_dns_zone_ids, get_properties,
                     update_dns_zone_record, update_failover_dns_record)


class SpinnakerDns:
    """Manipulate and create generated DNS record in Route53.

    Args:
        app (str): application name for DNS record
        env (str): Environment/Account for DNS record creation
        region (str): AWS Region for DNS record
        elb_subnet (str): Wether the DNS record is in a public or private zone
        prop_path (str): Path to the generated property files

    Returns:
        str: FQDN of application

    """

    def __init__(self, app=None, env=None, region=None, elb_subnet=None, prop_path=None):
        self.log = logging.getLogger(__name__)

        self.domain = DOMAIN
        self.env = env
        self.region = region
        self.elb_subnet = elb_subnet
        self.app = app

        self.generated = get_details(app, env=self.env, region=self.region)
        self.app_name = self.generated.app_name()

        self.properties = get_properties(properties_file=prop_path, env=self.env, region=self.region)
        self.dns_ttl = self.properties['dns']['ttl']
        self.header = {'content-type': 'application/json'}

    def create_elb_dns(self, regionspecific=False):
        """Create dns entries in route53.

        Args:
            regionspecific (bool): The DNS entry should have region on it
        Returns:
            str: Auto-generated DNS name for the Elastic Load Balancer.

        """
        if regionspecific:
            dns_elb = self.generated.dns()['elb_region']
        else:
            dns_elb = self.generated.dns()['elb']

        dns_elb_aws = find_elb(name=self.app_name, env=self.env, region=self.region)

        zone_ids = get_dns_zone_ids(env=self.env, facing=self.elb_subnet)

        self.log.info('Updating Application URL: %s', dns_elb)

        dns_kwargs = {
            'dns_name': dns_elb,
            'dns_name_aws': dns_elb_aws,
            'dns_ttl': self.dns_ttl,
        }

        for zone_id in zone_ids:
            self.log.debug('zone_id: %s', zone_id)
            update_dns_zone_record(self.env, zone_id, **dns_kwargs)

        return dns_elb

    def create_failover_dns(self, primary_region='us-east-1'):
        """Create dns entries in route53 for multiregion failover setups.

        Args:
            primary_region (str): primary AWS region for failover
        Returns:
            Auto-generated DNS name.
        """
        dns_record = self.generated.dns()['global']
        zone_ids = get_dns_zone_ids(env=self.env, facing=self.elb_subnet)

        elb_dns_aws = find_elb(name=self.app_name, env=self.env, region=self.region)
        elb_dns_zone_id = find_elb_dns_zone_id(name=self.app_name, env=self.env, region=self.region)

        if primary_region in elb_dns_aws:
            failover_state = 'PRIMARY'
        else:
            failover_state = 'SECONDARY'
        self.log.info("%s set as %s record", elb_dns_aws, failover_state)

        self.log.info('Updating Application Failover URL: %s', dns_record)

        dns_kwargs = {
            'dns_name': dns_record,
            'elb_dns_zone_id': elb_dns_zone_id,
            'elb_aws_dns': elb_dns_aws,
            'dns_ttl': self.dns_ttl,
            'failover_state': failover_state,
        }

        for zone_id in zone_ids:
            self.log.debug('zone_id: %s', zone_id)
            update_failover_dns_record(self.env, zone_id, **dns_kwargs)

        return dns_record
