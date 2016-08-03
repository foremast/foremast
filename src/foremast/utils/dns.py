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
