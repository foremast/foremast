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

"""Get available Subnets for specific Targets."""
import logging
from collections import defaultdict
from pprint import pformat

import requests
from tryagain import retries

from ..consts import API_URL, GATE_CLIENT_CERT, GATE_CA_BUNDLE
from ..exceptions import SpinnakerSubnetError, SpinnakerTimeout

LOG = logging.getLogger(__name__)


# TODO: split up into get_az, and get_subnet_id
@retries(max_attempts=6, wait=2.0, exceptions=SpinnakerTimeout)
def get_subnets(target='ec2',
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

    subnet_url = '{0}/subnets/aws'.format(API_URL)
    subnet_response = requests.get(subnet_url,
                                   verify=GATE_CA_BUNDLE,
                                   cert=GATE_CLIENT_CERT)

    if not subnet_response.ok:
        raise SpinnakerTimeout(subnet_response.text)

    subnet_list = subnet_response.json()

    for subnet in subnet_list:
        LOG.debug('Subnet: %(account)s\t%(region)s\t%(target)s\t%(vpcId)s\t'
                  '%(availabilityZone)s', subnet)

        if subnet['target'] == target:
            az = subnet['availabilityZone']
            account = subnet['account']
            subnet_region = subnet['region']
            subnet_id = subnet['id']
            try:
                if az not in account_az_dict[account][subnet_region]:
                    account_az_dict[account][subnet_region].append(az)
            except KeyError:
                account_az_dict[account][subnet_region] = [az]
            # get list of all subnet IDs with correct purpose
            if subnet['purpose'] == purpose:
                try:
                    subnet_id_dict[account][subnet_region].append(subnet_id)
                except KeyError:
                    subnet_id_dict[account][subnet_region] = [subnet_id]

            LOG.debug('%s regions: %s', account,
                      list(account_az_dict[account].keys()))

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
