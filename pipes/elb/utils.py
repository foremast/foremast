"""Get Availability Zones for all Subnets."""
import json
import logging
from collections import defaultdict
from pprint import pformat

import requests
from tryagain import retries


class SpinnakerTimeout(Exception):
    pass


LOG = logging.getLogger(__name__)


@retries(max_attempts=6, wait=10.0, exceptions=SpinnakerTimeout)
def get_subnets(gate_url='http://gate-api.build.example.com:8084',
                target='ec2',
                sample_file_name=''):
    """Gets all availability zones for a given target

        Params:
            gate_url: The URL to hit for gate API access
            target: the type of subnets to look up (ec2 or elb)
            sample_file_name (str): Sample JSON file contents override.

        Return:
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
        LOG.debug('Subnet:\n%s', pformat(subnet))

        if subnet['target'] == target:
            az = subnet['availabilityZone']
            account = subnet['account']
            region = subnet['region']

            LOG.debug('%s regions: %s', account,
                      list(account_az_dict[account].keys()))

            try:
                if az not in account_az_dict[account][region]:
                    account_az_dict[account][region].append(az)
            except KeyError:
                account_az_dict[account][region] = [az]

    LOG.debug('AZ dict:\n%s', pformat(dict(account_az_dict)))
    return account_az_dict


def main():
    """MAIN."""
    logging.basicConfig(level=logging.DEBUG)

    get_subnets()
    # get_subnets(sample_file_name='subnets_sample.json')


if __name__ == "__main__":
    main()
