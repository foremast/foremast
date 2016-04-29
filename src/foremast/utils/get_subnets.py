"""Get available Subnets for specific Targets."""
import json
import logging
from collections import defaultdict
from pprint import pformat

import requests
from tryagain import retries

from ..consts import API_URL
from ..exceptions import SpinnakerSubnetError, SpinnakerTimeout

LOG = logging.getLogger(__name__)


@retries(max_attempts=6, wait=10.0, exceptions=SpinnakerTimeout)
def get_subnets(gate_url=API_URL,
                target='ec2',
                env='',
                region='',
                sample_file_name=''):
    """Get all availability zones for a given target.

    Params:
        gate_url (str): Gate API url.
        target (str): Type of subnets to look up (ec2 or elb).
        env (str): Environment to look up.
        region (str): AWS Region to find Subnets for.
        sample_file_name (str): Sample JSON file contents override.

    Returns:
        az_dict: dictionary of  availbility zones, structured like
        { $account: { $region: [ $avaibilityzones ] } }
    """
    account_az_dict = defaultdict(defaultdict)

    if sample_file_name:
        with open(sample_file_name, 'rt') as file_handle:
            try:
                sample = file_handle.read()
            except FileNotFoundError:
                pass

        subnet_list = json.loads(sample)
    else:
        subnet_url = gate_url + "/subnets/aws"
        subnet_response = requests.get(subnet_url)

        if not subnet_response.ok:
            raise SpinnakerTimeout(subnet_response.text)

        subnet_list = subnet_response.json()

    LOG.debug('Subnet list: %s', subnet_list)

    for subnet in subnet_list:
        LOG.debug('Subnet: %(account)s\t%(region)s\t%(target)s\t%(vpcId)s\t'
                  '%(availabilityZone)s', subnet)

        if subnet['target'] == target:
            az = subnet['availabilityZone']
            account = subnet['account']
            region = subnet['region']

            try:
                if az not in account_az_dict[account][region]:
                    account_az_dict[account][region].append(az)
            except KeyError:
                account_az_dict[account][region] = [az]

            LOG.debug('%s regions: %s', account,
                      list(account_az_dict[account].keys()))

    LOG.debug('AZ dict:\n%s', pformat(dict(account_az_dict)))

    if all([env, region]):
        try:
            return {region: account_az_dict[env][region]}
        except KeyError:
            raise SpinnakerSubnetError(env=env, region=region)

    return account_az_dict
