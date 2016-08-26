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

"""Get VPC ID."""
import logging

import requests

from ..consts import API_URL, GATE_CA_BUNDLE, GATE_CLIENT_CERT
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
    response = requests.get(url,
                            verify=GATE_CA_BUNDLE,
                            cert=GATE_CLIENT_CERT)

    if not response.ok:
        raise SpinnakerVPCNotFound(response.text)

    vpcs = response.json()

    for vpc in vpcs:
        LOG.debug('VPC: %(name)s, %(account)s, %(region)s => %(id)s', vpc)
        if all([
                vpc['name'] == 'vpc',
                vpc['account'] == account,
                vpc['region'] == region
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
