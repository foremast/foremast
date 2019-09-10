
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
"""AWS Auto Scaling Group related utilities."""
import logging

import requests

from ..consts import API_URL, GATE_CA_BUNDLE, GATE_CLIENT_CERT

LOG = logging.getLogger(__name__)


def get_latest_server_group(env, app):
    """Finds the most recently deployed server group for the application.

    Returns:
        server_group (str): Name of the newest server group
    """
    api_url = "{0}/applications/{1}".format(API_URL, app)
    response = requests.get(api_url, verify=GATE_CA_BUNDLE, cert=GATE_CLIENT_CERT)

    for server_group in response.json()['clusters'][env]:
        LOG.debug("Server Group Response: %s", server_group)
        return server_group['serverGroups'][-1]
