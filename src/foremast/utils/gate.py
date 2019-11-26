#   Foremast - Pipeline Tooling
#
#   Copyright 2019 Redbox Automated Retail, LLC
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
"""Centralized Methods interacting with the Spinnaker Gate API."""
import logging

import requests

from ..consts import API_URL, GATE_AUTHENTICATION, GATE_CA_BUNDLE, GATE_CLIENT_CERT
from ..exceptions import GoogleIAPTokenError
from .google_iap import get_google_iap_bearer_token

LOG = logging.getLogger(__name__)
OAUTH_ENABLED = False


def gate_request(method='GET', uri=None, headers={}, data={}, params={}):
    """Make a request to Gate's API via various auth methods

    Args:
        method (str): Method to request Gate API; GET or POST
        uri (str): URI path to gate API
    """
    response = None

    url = '{host}{uri}'.format(host=API_URL, uri=uri)

    if GATE_AUTHENTICATION:
        if 'google_iap' in GATE_AUTHENTICATION:
            iap_response = get_google_iap_bearer_token(GATE_AUTHENTICATION['google_iap']['oauth_client_id'],
                                                       GATE_AUTHENTICATION['google_iap']['sa_credentials_path'])

            if 'id_token' not in iap_response:
                raise GoogleIAPTokenError

            headers['Authorization'] = 'Bearer {}'.format(iap_response['id_token'])
            LOG.info('Successfully set Google IAP Bearer Token in Request.')

        elif 'github' in GATE_AUTHENTICATION:
            github_token = GATE_AUTHENTICATION['github']['token']
            headers['Authorization'] = 'Bearer {}'.format(github_token)
            LOG.info('Successfully set Github Bearer Token in Request.')

    method = method.upper()
    if method == 'GET':
        response = requests.get(url, params=params, headers=headers, verify=GATE_CA_BUNDLE, cert=GATE_CLIENT_CERT)
    elif method == 'POST':
        response = requests.post(url, data=data, headers=headers, verify=GATE_CA_BUNDLE, cert=GATE_CLIENT_CERT)
    elif method == 'DELETE':
        response = requests.delete(url, headers=headers, verify=GATE_CA_BUNDLE, cert=GATE_CLIENT_CERT)
    else:
        raise NotImplementedError

    if response.status_code in ['401', '403', '503']:
        response.raise_for_status()

    LOG.info(response.content)
    return response
