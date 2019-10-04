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
"""Post a message to slack."""
import logging
import requests

from ..consts import API_URL, GATE_CA_BUNDLE, GATE_CLIENT_CERT

LOG = logging.getLogger(__name__)
OAUTH_ENABLED = False


def gate_request(method='GET', uri=None, headers=None, data=None, params=None):
    """Make a request to Gate's API via various auth methods

    Args:
        method (str): Method to request Gate API; GET or POST
        uri (str): URI path to gate API
    """
    response = None

    url = '{host}{uri}'.format(host=API_URL, uri=uri)

    if OAUTH_ENABLED:
        headers['Bearer'] = ""
        raise NotImplementedError

    if method == 'GET':
        response = requests.get(url, params=params, headers=headers, verify=GATE_CA_BUNDLE, cert=GATE_CLIENT_CERT)
    elif method == 'POST':
        response = requests.post(url, data=data, headers=headers, verify=GATE_CA_BUNDLE, cert=GATE_CLIENT_CERT)
    elif method == 'DELETE':
        response = requests.delete(url, headers=headers, verify=GATE_CA_BUNDLE, cert=GATE_CLIENT_CERT)
    else:
        raise NotImplementedError

    return response