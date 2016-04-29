"""DNS functions for deployment."""
import json
import logging
from pprint import pformat

import boto3.session
import requests
from tryagain import retries

from ..consts import API_URL
from ..exceptions import SpinnakerElbNotFound
from ..utils import get_app_details, get_template


class SpinnakerDns:
    """Manipulate Spinnaker Dns.

    Args:
        app_name: Str of application name add Security Group to.
    """

    def __init__(self, app_info):
        self.log = logging.getLogger(__name__)

        self.generated = get_app_details.get_details(app_info['app'],
                                                     env=app_info['env'])
        self.app_name = self.generated.app_name()

        # Add domain
        app_info.update({'domain': 'example.com'})
        self.app_info = app_info

        self.header = {'content-type': 'application/json'}

        env = boto3.session.Session(profile_name=self.app_info['env'])
        self.r53client = env.client('route53')

    @retries(max_attempts=10, wait=10.0, exceptions=SpinnakerElbNotFound)
    def get_app_aws_elb(self):
        """Get an application's AWS elb dns name."""
        url = '{0}/applications/{1}/loadBalancers'.format(API_URL,
                                                          self.app_name)
        response = requests.get(url)

        elb_dns = None

        if response.ok:
            accounts = response.json()
            for account in accounts:
                if account['account'] == self.app_info['env'] and \
                        account['region'] == self.app_info['region']:
                    elb_dns = account['dnsname']

        if not elb_dns:
            raise SpinnakerElbNotFound(
                'Elb for "{0}" in region {1} not found'.format(
                    self.app_name, self.app_info['region']))
        return elb_dns

    def create_elb_dns(self):
        """Create dns entries in route53.

        Args:
            app_catalog: A dictionary containing all parameters.

        Returns:
            Auto-generated DNS name for the Elastic Load Balancer.
        """
        dns_zone = '{env}.{domain}'.format(**self.app_info)

        dns_elb = self.generated.dns()['elb']
        dns_elb_aws = self.get_app_aws_elb()

        # get correct hosted zone
        zones = self.r53client.list_hosted_zones_by_name(DNSName=dns_zone)
        # self.log.debug('zones:\n%s', pformat(zones))

        zone_ids = []
        if len(zones['HostedZones']) > 1:
            for zone in zones['HostedZones']:
                # We will always add a private record. The elb subnet must be
                # specified as 'external' to get added publicly.
                if any([zone['Config']['PrivateZone'], self.app_info[
                        'elb_subnet'] in ('external')]):
                    self.log.info('Adding DNS record to %s zone', zone['Id'])
                    zone_ids.append(zone['Id'])

        self.log.info('Updating Application URL: %s', dns_elb)

        # This is what will be added to DNS
        dns_json = get_template(template_file='dns_upsert_template.json',
                                dns_elb=dns_elb,
                                dns_elb_aws=dns_elb_aws)

        for zone_id in zone_ids:
            self.log.debug('zone_id: %s', zone_id)

            response = self.r53client.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch=json.loads(dns_json), )

            self.log.debug('Dns upsert response: %s', pformat(response))

        return dns_elb
