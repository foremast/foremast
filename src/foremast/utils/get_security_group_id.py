"""Get security group id"""
import logging

import requests
from tryagain import retries

from ..consts import API_URL
from ..exceptions import SpinnakerSecurityGroupError
from .get_vpc_id import *

LOG = logging.getLogger(__name__)


@retries(max_attempts=5,
         wait=2,
         exceptions=(SpinnakerSecurityGroupError))
def get_security_group_id(name='', env='', region=''):
    """Get an security group ID"""
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
        msg = 'Security group (%s) not found'.format(name)
        raise SpinnakerSecurityGroupError(msg)

    LOG.info('Found: %s', security_group_id)
    return security_group_id
