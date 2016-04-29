"""DNS functions for deployment."""
import configparser
import json
import logging
import os
from pprint import pformat

import boto3.session
import gogoutils
import requests
from jinja2 import Environment, FileSystemLoader
from tryagain import retries

from ..consts import API_URL
from ..exceptions import SpinnakerApplicationListError, SpinnakerElbNotFound
from ..utils import get_configs, get_template


class SpinnakerDns:
    """Manipulate Spinnaker Dns.

    Args:
        app_name: Str of application name add Security Group to.
    """

    def __init__(self, app_info):
        self.log = logging.getLogger(__name__)

        self.app_name = self.app_exists(app_name=app_info['app'])

        # Add domain
        app_info.update({'domain': 'example.com'})
        self.app_info = app_info

        self.header = {'content-type': 'application/json'}

        env = boto3.session.Session(
            profile_name=self.app_info['env'])
        self.r53client = env.client('route53')

    def get_apps(self):
        """Gets all applications from spinnaker."""
        url = '{0}/applications'.format(API_URL)
        r = requests.get(url)
        if r.ok:
            return r.json()
        else:
            self.log.error(r.text)
            raise SpinnakerApplicationListError(r.text)

    def get_app_detail(self):
        """Retrieve app details"""

        url = '{0}/applications/{1}'.format(API_URL, self.app_name)
        r = requests.get(url)

        details = {}
        if r.ok:
            details.update(r.json())
            group = details['attributes'].get('repoProjectKey')
            project = details['attributes'].get('repoSlug')
            generator = gogoutils.Generator(
                    project=group,
                    repo=project,
                    env=self.app_info['env']
            )

            details.update({'dns_elb': generator.dns()['elb']})
            details.update({'dns_elb_aws': self.get_app_aws_elb()})
        else:
            raise SpinnakerAppNotFound('Application %s not found', self.app_name)

        self.log.debug('Application details: %s', details)

        return details

    @retries(max_attempts=10, wait=10.0, exceptions=SpinnakerElbNotFound)
    def get_app_aws_elb(self):
        """Get an application's AWS elb dns name"""
        url = '{0}/applications/{1}/loadBalancers'.format(API_URL, self.app_name)
        r = requests.get(url)

        elb_dns = None

        if r.ok:
            response = r.json()
            for account in response:
                if account['account'] == self.app_info['env'] and \
                        account['region'] == self.app_info['region']:
                    elb_dns = account['dnsname']

        if not elb_dns:
            raise SpinnakerElbNotFound('Elb for %s in region %s not found' %
                   (self.app_name, self.app_info['region']))
        return elb_dns

    def app_exists(self, app_name):
        """Checks to see if application already exists.

        Args:
            app_name: Str of application name to check.

        Returns:
            Str of application name

        Raises:
            SpinnakerAppNotFound
        """

        apps = self.get_apps()
        app_name = app_name.lower()
        for app in apps:
            if app['name'].lower() == app_name:
                self.log.info('Application %s found!', app_name)
                return app_name

        self.log.info('Application %s does not exist ... exiting', app_name)
        raise SpinnakerAppNotFound('Application "{0}" not found.'.format(
            app_name))

    def create_elb_dns(self):
        """ Creates dns entries in route53

        Args:
            app_catalog: A dictionary containing all parameters.

        Returns:
            Auto-generated DNS name for the Elastic Load Balancer.
        """

        dns_zone = '{env}.{domain}'.format(**self.app_info)

        app_details = self.get_app_detail()

        # get correct hosted zone
        zones = self.r53client.list_hosted_zones_by_name(
            DNSName=dns_zone)
        # self.log.debug('zones:\n%s', pformat(zones))

        zone_ids = []
        if len(zones['HostedZones']) > 1:
            for zone in zones['HostedZones']:
                # We will always add a private record. The elb subnet must be
                # specified as 'external' to get added publicly.
                if zone['Config']['PrivateZone'] or \
                                self.app_info['elb_subnet'] in (
                                'external'):
                    self.log.info('Adding DNS record to %s zone', zone['Id'])
                    zone_ids.append(zone['Id'])

        self.log.info('Updating Application URL: %s', app_details['dns_elb'])

        # This is what will be added to DNS
        dns_json = get_template(
            template_file='dns_upsert_template.json',
            data=app_details,
        )

        for zone_id in zone_ids:

            self.log.debug('zone_id: %s', zone_id)
            response = self.r53client.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch=json.loads(dns_json),
            )
            self.log.debug('Dns upsert response: %s', pformat(response))
        return app_details['dns_elb']
