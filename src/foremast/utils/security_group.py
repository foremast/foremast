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
"""Get security group id."""
import logging

from tryagain import retries

from ..consts import SECURITYGROUP_REPLACEMENTS
from ..exceptions import SpinnakerSecurityGroupError
from ..utils import gate_request
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

    uri = '/securityGroups/{0}/{1}/{2}?vpcId={3}'.format(env, region, name, vpc_id)
    response = gate_request(uri=uri)
    assert response.ok

    result = response.json()
    try:
        security_group_id = result['id']
    except KeyError:
        msg = 'Security group ({0}) not found'.format(name)
        raise SpinnakerSecurityGroupError(msg)

    LOG.info('Found: %s', security_group_id)
    return security_group_id


def remove_duplicate_sg(security_groups):
    """Removes duplicate Security Groups that share a same name alias

    Args:
        security_groups (list): A list of security group id to compare against SECURITYGROUP_REPLACEMENTS

    Returns:
        security_groups (list): A list of security groups with duplicate aliases removed
    """
    for each_sg, duplicate_sg_name in SECURITYGROUP_REPLACEMENTS.items():
        if each_sg in security_groups and duplicate_sg_name in security_groups:
            LOG.info('Duplicate SG found. Removing %s in favor of %s.', duplicate_sg_name, each_sg)
            security_groups.remove(duplicate_sg_name)

    return security_groups
