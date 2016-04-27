"""Get Availability Zones for all Subnets."""
import json
import logging
from collections import defaultdict
from exceptions import (SpinnakerTaskError, SpinnakerVPCIDNotFound,
                        SpinnakerVPCNotFound)
from pprint import pformat

import requests
from tryagain import retries


class SpinnakerTimeout(Exception):
    pass


LOG = logging.getLogger(__name__)

GATE_URL = "http://gate-api.build.example.com:8084"
HEADERS = {'Content-Type': 'application/json', 'Accept': '*/*'}


def get_vpc_id(account, region):
    """Get vpc id.

    Args:
        account (str): AWS account name.
        region (str): Region name, e.g. us-east-1.

    Returns:
        str: ID for the requested _account_ in _region_.
    """
    url = '{0}/vpcs'.format(GATE_URL)
    response = requests.get(url)

    LOG.debug('VPC response:\n%s', response.text)

    if response.ok:
        for vpc in response.json():
            LOG.debug('VPC: %(name)s, %(account)s, %(region)s => %(id)s', vpc)
            if all([vpc['name'] == 'vpc', vpc['account'] == account, vpc[
                    'region'] == region]):
                LOG.info('Found VPC ID for %s in %s: %s', account, region,
                         vpc['id'])
                return vpc['id']
        else:
            raise SpinnakerVPCIDNotFound(response.text)
    else:
        LOG.error(response.text)
        raise SpinnakerVPCNotFound(response.text)


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
    return account_az_dict


@retries(max_attempts=10, wait=10, exceptions=Exception)
def check_task(taskid, app_name):
    """Check ELB creation status.
    Args:
        taskid: the task id returned from create_elb.
        app_name: application name related to this task.

    Returns:
        polls for task status.
    """
    try:
        taskurl = taskid.get('ref', '0000')
    except AttributeError:
        taskurl = taskid

    taskid = taskurl.split('/tasks/')[-1]

    LOG.info('Checking taskid %s', taskid)

    url = '{0}/applications/{1}/tasks/{2}'.format(GATE_URL, app_name, taskid)
    task_response = requests.get(url, headers=HEADERS)

    LOG.debug(task_response.json())

    if not task_response.ok:
        raise Exception
    else:
        task_state = task_response.json()
        status = task_state['status']
        LOG.info('Current task status: %s', status)

        if status == 'SUCCEEDED':
            return status
        elif status == 'TERMINAL':
            raise SpinnakerTaskError(task_state)
        else:
            raise Exception


def main():
    """MAIN."""
    logging.basicConfig(level=logging.DEBUG)

    get_subnets()
    # get_subnets(sample_file_name='subnets_sample.json')
    get_vpc_id('dev', 'us-east-1')


if __name__ == "__main__":
    main()
