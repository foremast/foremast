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

"""Search for ELB DNS name."""
import logging

import requests
from tryagain import retries

from ..consts import API_URL, GATE_CLIENT_CERT, GATE_CA_BUNDLE
from ..exceptions import SpinnakerElbNotFound

LOG = logging.getLogger(__name__)


@retries(max_attempts=5,
         wait=2,
         exceptions=(AssertionError, SpinnakerElbNotFound))
def find_elb(name='', env='', region=''):
    """Get an application's AWS elb dns name.

    Args:
        name (str): ELB name
        env (str): Environment/account of ELB
        region (str): AWS Region

    Returns:
        str: elb DNS record
    """
    LOG.info('Find %s ELB in %s [%s].', name, env, region)

    url = '{0}/applications/{1}/loadBalancers'.format(API_URL, name)
    response = requests.get(url,
                            verify=GATE_CA_BUNDLE,
                            cert=GATE_CLIENT_CERT)
    assert response.ok

    elb_dns = None
    accounts = response.json()
    for account in accounts:
        if account['account'] == env and account['region'] == region:
            elb_dns = account['dnsname']
            break
    else:
        raise SpinnakerElbNotFound(
            'Elb for "{0}" in region {1} not found'.format(name, region))

    LOG.info('Found: %s', elb_dns)
    return elb_dns
