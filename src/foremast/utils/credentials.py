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

"""Retrieve Account Credential from Gate API."""
import logging

import murl
import requests

from ..consts import API_URL, GATE_CLIENT_CERT, GATE_CA_BUNDLE

LOG = logging.getLogger(__name__)


def get_env_credential(env='dev'):
    """Get Account Credential from Spinnaker for *env*.

    Args:
        env (str): Environment name to find credentials for.

    Returns:
        dict: Complete credentials for *env*::

            {
                'accountId': '123098123',
                'accountType': 'dev',
                'assumeRole': 'role/spinnakerManaged',
                'bastionEnabled': False,
                'challengeDestructiveActions': False,
                'cloudProvider': 'aws',
                'defaultKeyPair': 'dev_access',
                'discoveryEnabled': False,
                'eddaEnabled': False,
                'environment': 'dev',
                'front50Enabled': False,
                'name': 'dev',
                'primaryAccount': False,
                'provider': 'aws',
                'regions': [
                    {
                        'availabilityZones': ['us-east-1b', 'us-east-1c',
                                              'us-east-1d', 'us-east-1e'],
                        'deprecated': False,
                        'name': 'us-east-1',
                        'preferredZones':
                        ['us-east-1b', 'us-east-1c', 'us-east-1d', 'us-east-1e'
                         ]
                    }, {
                        'availabilityZones':
                        ['us-west-2a', 'us-west-2b', 'us-west-2c'],
                        'deprecated': False,
                        'name': 'us-west-2',
                        'preferredZones':
                        ['us-west-2a', 'us-west-2b', 'us-west-2c']
                    }
                ],
                'requiredGroupMembership': [],
                'sessionName': 'Spinnaker',
                'type': 'aws'
            }
    """
    url = murl.Url(API_URL)
    url.path = '/'.join(['credentials', env])
    credential_response = requests.get(url.url,
                                       verify=GATE_CA_BUNDLE,
                                       cert=GATE_CLIENT_CERT)

    assert credential_response.ok, 'Could not get credentials from Spinnaker.'

    credential = credential_response.json()
    LOG.debug('Credentials found:\n%s', credential)
    return credential
