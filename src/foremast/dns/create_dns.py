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

"""Module to create dynamically generated DNS record in route53"""
import json
import logging
from pprint import pformat

import boto3.session

from ..utils import find_elb, get_app_details, get_template, get_properties


class SpinnakerDns:
    """Manipulate and create generated DNS record in Route53.

    Args:
        app_name (str): application name for DNS record
        env (str): Environment/Account for DNS record creation
        region (str): AWS Region for DNS record
        elb_subnet (str): Wether the DNS record is in a public or private zone
        prop_path (str): Path to the generated property files
    """

    def __init__(self, app=None, env=None, region=None, elb_subnet=None, prop_path=None):
        self.log = logging.getLogger(__name__)

        self.generated = get_app_details.get_details(app, env=env)
        self.app_name = self.generated.app_name()

        # Add domain
        self.domain = 'example.com'
        self.env = env
        self.region = region
        self.elb_subnet = elb_subnet
        self.properties = get_properties(properties_file=prop_path, env=env)
        self.header = {'content-type': 'application/json'}
        env = boto3.session.Session(profile_name=self.env)
        self.r53client = env.client('route53')

    def create_elb_dns(self):
        """Create dns entries in route53.

        Returns:
            Auto-generated DNS name for the Elastic Load Balancer.
        """
        dns_zone = '{}.{}'.format(self.env, self.domain)

        dns_elb = self.generated.dns()['elb']
        dns_elb_aws = find_elb(name=self.app_name,
                               env=self.env,
                               region=self.region)
        dns_ttl = self.properties['dns']['ttl']

        # get correct hosted zone
        zones = self.r53client.list_hosted_zones_by_name(DNSName=dns_zone)
        # self.log.debug('zones:\n%s', pformat(zones))

        zone_ids = []
        if len(zones['HostedZones']) > 1:
            for zone in zones['HostedZones']:
                # We will always add a private record. The elb subnet must be
                # specified as 'external' to get added publicly.
                if any([zone['Config']['PrivateZone'], self.elb_subnet in (
                        'external')]):
                    self.log.info('Adding DNS record to %s zone', zone['Id'])
                    zone_ids.append(zone['Id'])

        self.log.info('Updating Application URL: %s', dns_elb)

        # This is what will be added to DNS
        dns_json = get_template(template_file='infrastructure/dns_upsert_template.json',
                                dns_elb=dns_elb,
                                dns_elb_aws=dns_elb_aws,
                                dns_ttl=dns_ttl)

        # TODO: Verify zone_id matches the domain we are updating There are
        # cases where more than 2 zones are in the account and we need to
        # account for that.
        for zone_id in zone_ids:
            self.log.debug('zone_id: %s', zone_id)

            # TODO: boto3 call can fail with botocore.exceptions.ClientError,
            # need to retry
            response = self.r53client.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch=json.loads(dns_json), )

            self.log.debug('Dns upsert response: %s', pformat(response))

        return dns_elb
