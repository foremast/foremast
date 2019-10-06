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
"""Get available Subnets for specific Targets."""
import logging
from collections import defaultdict
from pprint import pformat

from tryagain import retries

from ..exceptions import SpinnakerSubnetError, SpinnakerTimeout
from ..utils.gate import gate_request

LOG = logging.getLogger(__name__)


# TODO: split up into get_az, and get_subnet_id
@retries(max_attempts=6, wait=2.0, exceptions=SpinnakerTimeout)  # noqa
def get_subnets(
        target='ec2',
        purpose='internal',
        env='',
        region='', ):
    """Get all availability zones for a given target.

    Args:
        target (str): Type of subnets to look up (ec2 or elb).
        env (str): Environment to look up.
        region (str): AWS Region to find Subnets for.

    Returns:
        az_dict: dictionary of  availbility zones, structured like
        { $region: [ $avaibilityzones ] }
        or
        { $account: $region: [ $availabilityzone] }
    """
    account_az_dict = defaultdict(defaultdict)
    subnet_id_dict = defaultdict(defaultdict)

    uri = '/subnets/aws'
    subnet_response = gate_request(uri=uri)

    if not subnet_response.ok:
        raise SpinnakerTimeout(subnet_response.text)

    subnet_list = subnet_response.json()
    for subnet in subnet_list:
        LOG.debug('Subnet Response: %s', subnet)

        if subnet.get('target', '') == target:
            availability_zone = subnet['availabilityZone']
            account = subnet['account']
            subnet_region = subnet['region']
            subnet_id = subnet['id']
            try:
                if availability_zone not in account_az_dict[account][subnet_region]:
                    account_az_dict[account][subnet_region].append(availability_zone)
            except KeyError:
                account_az_dict[account][subnet_region] = [availability_zone]
            # get list of all subnet IDs with correct purpose
            if subnet['purpose'] == purpose:
                try:
                    subnet_id_dict[account][subnet_region].append(subnet_id)
                except KeyError:
                    subnet_id_dict[account][subnet_region] = [subnet_id]

            LOG.debug('%s regions: %s', account, list(account_az_dict[account].keys()))

    if all([env, region]):
        try:
            region_dict = {region: account_az_dict[env][region]}
            region_dict['subnet_ids'] = {region: subnet_id_dict[env][region]}
            LOG.debug('Region dict: %s', region_dict)
            return region_dict
        except KeyError:
            raise SpinnakerSubnetError(env=env, region=region)

    LOG.debug('AZ dict:\n%s', pformat(dict(account_az_dict)))

    return account_az_dict
