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
"""Retrieve Route 53 Hosted Zone IDs."""
import json
import logging
from pprint import pformat

import boto3
from boto3.exceptions import botocore

from ..consts import DOMAIN
from ..exceptions import PrimaryDNSRecordNotFound
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
            response = client.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch=json.loads(dns_json), )
            LOG.info('Upserted DNS record %s (%s) in Hosted Zone %s (%s)', dns_name, dns_name_aws, zone_id, zone_name)
        except botocore.exceptions.ClientError as error:
            LOG.info('Error creating DNS record %s (%s) in Hosted Zone %s (%s)', dns_name, dns_name_aws, zone_id,
                     zone_name)
            LOG.debug(error)
    else:
        LOG.info('Skipping creating DNS record %s in non-matching Hosted Zone %s (%s)', dns_name, zone_id, zone_name)

    LOG.debug('Route53 JSON Response: \n%s', pformat(response))


def find_existing_record(env, zone_id, dns_name, check_key=None, check_value=None):
    """Check if a specific DNS record exists.

    Args:
        env (str): Deployment environment.
        zone_id (str): Route53 zone id.
        dns_name (str): FQDN of application's dns entry to add/update.
        check_key(str): Key to look for in record. Example: "Type"
        check_value(str): Value to look for with check_key. Example: "CNAME"

    Returns:
        json: Found Record. Returns None if no record found

    """
    client = boto3.Session(profile_name=env).client('route53')
    pager = client.get_paginator('list_resource_record_sets')
    existingrecord = None
    for rset in pager.paginate(HostedZoneId=zone_id):
        for record in rset['ResourceRecordSets']:
            if check_key:
                if record['Name'].rstrip('.') == dns_name and record.get(check_key) == check_value:
                    LOG.info("Found existing record: %s", record)
                    existingrecord = record
                    break
    return existingrecord


def delete_existing_cname(env, zone_id, dns_name):
    """Delete an existing CNAME record.

    This is used when updating to multi-region for deleting old records. The
    record can not just be upserted since it changes types.

    Args:
        env (str): Deployment environment.
        zone_id (str): Route53 zone id.
        dns_name (str): FQDN of application's dns entry to add/update.
    """
    client = boto3.Session(profile_name=env).client('route53')
    startrecord = None
    newrecord_name = dns_name
    startrecord = find_existing_record(env, zone_id, newrecord_name, check_key='Type', check_value='CNAME')
    if startrecord:
        LOG.info("Deleting old record: %s", newrecord_name)
        _response = client.change_resource_record_sets(
            HostedZoneId=zone_id, ChangeBatch={'Changes': [{
                'Action': 'DELETE',
                'ResourceRecordSet': startrecord
            }]})
        LOG.debug('Response from deleting %s: %s', dns_name, _response)


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

    # Check that the primary record exists
    failover_state = kwargs.get('failover_state')
    if failover_state.lower() != 'primary':
        primary_record = find_existing_record(env, zone_id, dns_name, check_key='Failover', check_value='PRIMARY')
        if not primary_record:
            raise PrimaryDNSRecordNotFound("Primary Failover DNS record not found: {}".format(dns_name))

    if dns_name and dns_name.endswith(zone_name):
        dns_json = get_template(template_file='infrastructure/dns_failover_upsert.json.j2', **kwargs)
        LOG.info('Attempting to create DNS Failover record %s (%s) in Hosted Zone %s (%s)', dns_name,
                 kwargs['elb_aws_dns'], zone_id, zone_name)
        try:
            delete_existing_cname(env, zone_id, dns_name)
            response = client.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch=json.loads(dns_json), )
            LOG.info('Upserted DNS Failover record %s (%s) in Hosted Zone %s (%s)', dns_name, kwargs['elb_aws_dns'],
                     zone_id, zone_name)
        except botocore.exceptions.ClientError as error:
            LOG.info('Error creating DNS Failover record %s (%s) in Hosted Zone %s (%s)', dns_name,
                     kwargs['elb_aws_dns'], zone_id, zone_name)
            LOG.debug(error)
    else:
        LOG.info('Skipping creating DNS record %s in non-matching Hosted Zone %s (%s)', dns_name, zone_id, zone_name)

    LOG.debug('Route53 JSON Response: \n%s', pformat(response))
