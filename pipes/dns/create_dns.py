"""DNS functions for deployment."""
import logging
from pprint import pformat
import argparse
import os
import configparser
import json

import gogoutils
from jinja2 import Environment, FileSystemLoader
import requests
import boto3.session


class SpinnakerAppNotFound(Exception):
    pass


class SpinnakerApplicationListError(Exception):
    pass


class SpinnakerDnsCreationFailed(Exception):
    pass


class SpinnakerDns:
    """Manipulate Spinnaker Dns.

    Args:
        app_name: Str of application name add Security Group to.
    """

    def __init__(self, app_info):
        self.log = logging.getLogger(__name__)

        self.here = os.path.dirname(os.path.realpath(__file__))
        self.config = self.get_configs()
        self.gate_url = self.config['spinnaker']['gate_url']
        self.app_name = self.app_exists(app_name=app_info['name'])

        # Add domain
        app_info.update({'domain': 'example.com'})
        self.app_info = app_info

        self.header = {'content-type': 'application/json'}

        env = boto3.session.Session(
            profile_name=self.app_info['environment'])
        self.r53client = env.client('route53')

    def get_configs(self):
        """Get main configuration.

        Returns:
            configparser.ConfigParser object with configuration loaded.
        """
        config = configparser.ConfigParser()
        configpath = "{}/../../configs/spinnaker.conf".format(self.here)
        config.read(configpath)

        self.log.debug('Configuration sections found: %s', config.sections())
        return config

    def get_template(self, template_name='', template_dict=None):
        """Get Jinja2 Template _template_name_.

        Args:
            template_name: Str of template name to retrieve.
            template_dict: Dict to use for template rendering.

        Returns:
            Dict of rendered JSON to send to Spinnaker.
        """
        templatedir = "{}/../../templates".format(self.here)
        jinja_env = Environment(loader=FileSystemLoader(templatedir))
        template = jinja_env.get_template(template_name)

        rendered_json = json.loads(template.render(**template_dict))
        self.log.debug('Rendered template: %s', rendered_json)
        return rendered_json

    def get_apps(self):
        """Gets all applications from spinnaker."""
        url = '{0}/applications'.format(self.gate_url)
        r = requests.get(url)
        if r.ok:
            return r.json()
        else:
            self.log.error(r.text)
            raise SpinnakerApplicationListError(r.text)

    def get_app_detail(self):
        """Retrieve app details"""

        url = '{0}/applications/{1}'.format(self.gate_url, self.app_name)
        r = requests.get(url)

        details = {}
        if r.ok:
            details.update(r.json())
            git_url = details['attributes'].get('repoProjectKey')
            group, project = gogoutils.Parser(git_url).parse_url()
            generator = gogoutils.Generator(
                    project=group,
                    repo=project,
                    env=self.app_info['environment']
            )

            details.update({'dns_elb': generator.dns()['elb']})
            details.update({'dns_elb_aws': self.get_app_aws_elb()})
        else:
            raise SpinnakerAppNotFound('Application %s not found', self.app_name)

        self.log.debug('Application details: %s', details)

        return details

    def get_app_aws_elb(self):
        """Get an application's AWS elb dns name"""
        url = '{0}/applications/{1}/loadBalancers'.format(self.gate_url, self.app_name)
        r = requests.get(url)

        elb_dns = None

        if r.ok:
            response = r.json()
            for account in response:
                if account['account'] == self.app_info['environment']:
                    elb_dns = account['dnsname']

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

        dns_zone = '{environment}.{domain}'.format(**self.app_info)

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
                                self.app_info['config']['elb']['subnet_purpose'] in (
                                'external'):
                    self.log.info('Adding DNS record to %s zone', zone['Id'])
                    zone_ids.append(zone['Id'])

        self.log.info('Updating Application URL: %s', app_details['dns_elb'])

        # This is what will be added to DNS
        dns_json = self.get_template(
            template_name='dns_upsert_template.json',
            template_dict=app_details,
        )

        self.log.debug('Dns json to send: %s', pformat(dns_json))

        for zone_id in zone_ids:

            self.log.debug('zone_id: %s', zone_id)
            response = self.r53client.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch=dns_json,
            )
            self.log.debug('Dns upsert response: %s', pformat(response))
        return app_details['dns_elb']


def main():
    """Run newer stuffs."""
    logging.basicConfig(format='%(asctime)s %(message)s')
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument('-d',
                        '--debug',
                        action='store_true',
                        help='DEBUG output')
    parser.add_argument("--name",
                        help="The application name to create",
                        required=True)
    parser.add_argument("--region",
                        help="The region to create the security group",
                        required=True)
    parser.add_argument("--environment",
                        help="The environment to create the security group",
                        required=True)
    args = parser.parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)

    log.debug('Parsed arguments: %s', args)

    # Dictionary containing application info. This is passed to the class for processing
    appinfo = {
        'name': args.name,
        'region': args.region,
        'environment': args.environment,
    }

    # TODO: Get actual items from application.json
    appinfo.update({'config': {'elb': {'subnet_purpose': 'internal'}}})

    spinnakerapps = SpinnakerDns(app_info=appinfo)
    spinnakerapps.create_elb_dns()


if __name__ == "__main__":
    main()
