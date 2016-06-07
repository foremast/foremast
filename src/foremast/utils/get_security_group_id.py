"""Get security group id"""
import logging

import requests
from tryagain import retries

from ..consts import API_URL
from ..exceptions import SpinnakerSecurityGroupError
from .get_vpc_id import get_vpc_id

LOG = logging.getLogger(__name__)


@retries(max_attempts=5, wait=2, exceptions=(SpinnakerSecurityGroupError))
def get_security_group_id(name='', env='', region=''):
    """Get a security group ID.

    Args:
        name (str): Security Group name to find.
        env (str): Deployment environment to search.
        region (str): AWS Region to search.

    Returns:
        str: ID of Security Group, e.g. sg-xxxx.

    Raises:
        AssertionError: Call to Gate API was not successful.
        SpinnakerSecurityGroupError: Security Group _name_ was not found for
            _env_ in _region_.
    """
    vpc_id = get_vpc_id(env, region)

    LOG.info('Find %s sg in %s [%s] in %s', name, env, region, vpc_id)

    url = '{0}/securityGroups/{1}/{2}/{3}?vpcId={4}'.format(
        API_URL, env, region, name, vpc_id)
    response = requests.get(url)

    assert response.ok

    result = response.json()
    try:
        security_group_id = result['id']
    except KeyError:
        msg = 'Security group ({0}) not found'.format(name)
        raise SpinnakerSecurityGroupError(msg)

    LOG.info('Found: %s', security_group_id)
    return security_group_id
