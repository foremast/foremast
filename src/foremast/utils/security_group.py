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
"""Get security group id."""
import logging

import requests
from tryagain import retries

from ..consts import API_URL, GATE_CA_BUNDLE, GATE_CLIENT_CERT
from ..exceptions import SpinnakerSecurityGroupError
from .vpc import get_vpc_id

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

    url = '{0}/securityGroups/{1}/{2}/{3}?vpcId={4}'.format(API_URL, env, region, name, vpc_id)
    response = requests.get(url, verify=GATE_CA_BUNDLE, cert=GATE_CLIENT_CERT)
    assert response.ok

    result = response.json()
    try:
        security_group_id = result['id']
    except KeyError:
        msg = 'Security group ({0}) not found'.format(name)
        raise SpinnakerSecurityGroupError(msg)

    LOG.info('Found: %s', security_group_id)
    return security_group_id
