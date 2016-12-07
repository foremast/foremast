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
"""Retrieve Route 53 Hosted Zone IDs."""
import json
import logging
from pprint import pformat

import boto3
from boto3.exceptions import botocore

from ..consts import DOMAIN
from ..utils import get_template

LOG = logging.getLogger(__name__)


def get_dns_zone_ids(env='dev', facing='internal'):
    """Get Route 53 Hosted Zone IDs for _env_.

    Args:
        env (str): Deployment environment.
        facing (str): Type of ELB, external or internal.

    Returns:
        list: Hosted Zone IDs for _env_. Only *PrivateZone* when _facing_ is
        internal.
    """
    client = boto3.Session(profile_name=env).client('route53')

    zones = client.list_hosted_zones_by_name(DNSName='.'.join([env, DOMAIN]))

    zone_ids = []
    for zone in zones['HostedZones']:
        LOG.debug('Found Hosted Zone: %s', zone)

        if facing == 'external' or zone['Config']['PrivateZone']:
            LOG.info('Using %(Id)s for "%(Name)s", %(Config)s', zone)
            zone_ids.append(zone['Id'])

    LOG.debug('Zone IDs: %s', zone_ids)
    return zone_ids


def update_dns_zone_record(env, zone_id, **kwargs):
    """Create a Route53 CNAME record in _env_ zone.

    Args:
        env (str): Deployment environment.
        zone_id (str): Route53 zone id.

    Keyword Args:
        dns_name (str): FQDN of application's dns entry to add/update.
        dns_name_aws (str): FQDN of AWS resource
        dns_ttl (int): DNS time-to-live (ttl)
    """
    client = boto3.Session(profile_name=env).client('route53')
    response = {}

    hosted_zone_info = client.get_hosted_zone(Id=zone_id)
    zone_name = hosted_zone_info['HostedZone']['Name'].rstrip('.')
    dns_name = kwargs.get('dns_name')

    if dns_name and dns_name.endswith(zone_name):
        dns_name_aws = kwargs.get('dns_name_aws')
        # This is what will be added to DNS
        dns_json = get_template(template_file='infrastructure/dns_upsert.json.j2', **kwargs)
        LOG.info('Attempting to create DNS record %s (%s) in Hosted Zone %s (%s)', dns_name, dns_name_aws, zone_id,
                 zone_name)
        try:
            response = client.change_resource_record_sets(HostedZoneId=zone_id, ChangeBatch=json.loads(dns_json), )
            LOG.info('Upserted DNS record %s (%s) in Hosted Zone %s (%s)', dns_name, dns_name_aws, zone_id, zone_name)
        except botocore.exceptions.ClientError as e:
            LOG.info('Error creating DNS record %s (%s) in Hosted Zone %s (%s)', dns_name, dns_name_aws, zone_id,
                     zone_name)
            LOG.debug(e)
    else:
        LOG.info('Skipping creating DNS record %s in non-matching Hosted Zone %s (%s)', dns_name, zone_id, zone_name)

    LOG.debug('Route53 JSON Response: \n%s', pformat(response))


def update_failover_dns_record(env, zone_id, **kwargs):
    """Create a Failover Route53 alias record in _env_ zone.

    Args:
        env (str): Deployment environment.
        zone_id (str): Route53 zone id.

    Keyword Args:
        dns_name (str): FQDN of application's dns entry to add/update.
        dns_ttl (int): DNS time-to-live (ttl)
        elb_aws_dns (str): DNS A Record of ELB from AWS
        elb_dns_zone_id (str): Zone ID of ELB DNS
        failover_state (str): if the record is primary or secondary
        primary_region (str): Primary AWS region for DNS
    """
    client = boto3.Session(profile_name=env).client('route53')
    response = {}

    hosted_zone_info = client.get_hosted_zone(Id=zone_id)
    zone_name = hosted_zone_info['HostedZone']['Name'].rstrip('.')
    dns_name = kwargs.get('dns_name')

    if dns_name and dns_name.endswith(zone_name):
        dns_json = get_template(template_file='infrastructure/dns_failover_upsert.json.j2', **kwargs)
        LOG.info('Attempting to create DNS Failover record %s (%s) in Hosted Zone %s (%s)', dns_name,
                 kwargs['elb_aws_dns'], zone_id, zone_name)
        try:
            response = client.change_resource_record_sets(HostedZoneId=zone_id, ChangeBatch=json.loads(dns_json), )
            LOG.info('Upserted DNS Failover record %s (%s) in Hosted Zone %s (%s)', dns_name, kwargs['elb_aws_dns'],
                     zone_id, zone_name)
        except botocore.exceptions.ClientError as e:
            LOG.info('Error creating DNS Failover record %s (%s) in Hosted Zone %s (%s)', dns_name,
                     kwargs['elb_aws_dns'], zone_id, zone_name)
            LOG.debug(e)
    else:
        LOG.info('Skipping creating DNS record %s in non-matching Hosted Zone %s (%s)', dns_name, zone_id, zone_name)

    LOG.debug('Route53 JSON Response: \n%s', pformat(response))
