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
"""Get VPC ID."""
import logging

from ..consts import VPC_NAME
from ..exceptions import SpinnakerVPCIDNotFound, SpinnakerVPCNotFound
from ..utils.gate import gate_request

LOG = logging.getLogger(__name__)


def get_vpc_id(account, region):
    """Get VPC ID configured for ``account`` in ``region``.

    Args:
        account (str): AWS account name.
        region (str): Region name, e.g. us-east-1.

    Returns:
        str: VPC ID for the requested ``account`` in ``region``.

    Raises:
        :obj:`foremast.exceptions.SpinnakerVPCIDNotFound`: VPC ID not found for
            ``account`` in ``region``.
        :obj:`foremast.exceptions.SpinnakerVPCNotFound`: Spinnaker has no VPCs
            configured.

    """
    uri = '/networks/aws'
    response = gate_request(uri=uri)

    if not response.ok:
        raise SpinnakerVPCNotFound(response.text)

    vpcs = response.json()

    for vpc in vpcs:
        LOG.debug('VPC Response: %s', vpc)
        if 'name' in vpc and all([vpc['name'] == VPC_NAME, vpc['account'] == account, vpc['region'] == region]):
            LOG.info('Found VPC ID for %s in %s: %s', account, region, vpc['id'])
            vpc_id = vpc['id']
            break
    else:
        LOG.fatal('VPC list: %s', vpcs)
        raise SpinnakerVPCIDNotFound('No VPC available for {0} [{1}].'.format(account, region))

    return vpc_id
