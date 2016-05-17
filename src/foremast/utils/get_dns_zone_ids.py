"""Retrieve Route 53 Hosted Zone IDs."""
import logging

import boto3

from ..consts import DOMAIN

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
