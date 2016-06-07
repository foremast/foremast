"""DNS functions for deployment."""
import json
import logging
from pprint import pformat

import boto3.session

from ..utils import find_elb, get_app_details, get_template


class SpinnakerDns:
    """Manipulate Spinnaker Dns.

    Args:
        app_name: Str of application name add Security Group to.
    """

    def __init__(self, app=None, env=None, region=None, elb_subnet=None):
        self.log = logging.getLogger(__name__)

        self.generated = get_app_details.get_details(app,
                                                     env=env)
        self.app_name = self.generated.app_name()

        # Add domain
        self.domain = 'example.com'
        self.env = env
        self.region = region
        self.elb_subnet = elb_subnet

        self.header = {'content-type': 'application/json'}

        env = boto3.session.Session(profile_name=self.env)
        self.r53client = env.client('route53')

    def create_elb_dns(self):
        """Create dns entries in route53.

        Args:
            app_catalog: A dictionary containing all parameters.

        Returns:
            Auto-generated DNS name for the Elastic Load Balancer.
        """
        dns_zone = '{}.{}'.format(self.env, self.domain)

        dns_elb = self.generated.dns()['elb']
        dns_elb_aws = find_elb(name=self.app_name,
                               env=self.env,
                               region=self.region)

        # get correct hosted zone
        zones = self.r53client.list_hosted_zones_by_name(DNSName=dns_zone)
        # self.log.debug('zones:\n%s', pformat(zones))

        zone_ids = []
        if len(zones['HostedZones']) > 1:
            for zone in zones['HostedZones']:
                # We will always add a private record. The elb subnet must be
                # specified as 'external' to get added publicly.
                if any([zone['Config']['PrivateZone'], self.elb_subnet in ('external')]):
                    self.log.info('Adding DNS record to %s zone', zone['Id'])
                    zone_ids.append(zone['Id'])

        self.log.info('Updating Application URL: %s', dns_elb)

        # This is what will be added to DNS
        dns_json = get_template(template_file='dns_upsert_template.json',
                                dns_elb=dns_elb,
                                dns_elb_aws=dns_elb_aws)

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
