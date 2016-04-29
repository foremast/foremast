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

    LOG.debug('VPC response:\n%s', response.text)

    if not response.ok:
        LOG.error(response.text)
        raise SpinnakerVPCNotFound(response.text)

    for vpc in response.json():
        LOG.debug('VPC: %(name)s, %(account)s, %(region)s => %(id)s', vpc)
        if all([vpc['name'] == 'vpc', vpc['account'] == account, vpc[
                'region'] == region]):
            LOG.info('Found VPC ID for %s in %s: %s', account, region,
                     vpc['id'])
            return vpc['id']
    else:
        raise SpinnakerVPCIDNotFound(response.text)
