"""Get VPC ID."""
import logging

import requests

from ..consts import API_URL
from ..exceptions import SpinnakerVPCIDNotFound, SpinnakerVPCNotFound

LOG = logging.getLogger(__name__)


def get_vpc_id(account, region):
    """Get vpc id.

    Args:
        account (str): AWS account name.
        region (str): Region name, e.g. us-east-1.

    Returns:
        str: ID for the requested _account_ in _region_.
    """
    url = '{0}/vpcs'.format(API_URL)
    response = requests.get(url)

    if not response.ok:
        raise SpinnakerVPCNotFound(response.text)

    vpcs = response.json()

    vpc_id = ''
    for vpc in vpcs:
        LOG.debug('VPC: %(name)s, %(account)s, %(region)s => %(id)s', vpc)
        if all([
                vpc['name'] == 'vpc', vpc['account'] == account, vpc[
                    'region'] == region
        ]):
            LOG.info('Found VPC ID for %s in %s: %s', account, region,
                     vpc['id'])
            vpc_id = vpc['id']
            break
    else:
        LOG.fatal('VPC list: %s', vpcs)
        raise SpinnakerVPCIDNotFound('No VPC available for {0} [{1}].'.format(
            account, region))

    return vpc_id
