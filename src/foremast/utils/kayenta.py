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
"""Set of utility functions for Spinnaker's kayenta canary service"""
import requests

from ..exceptions import SpinnakerPipelineCreationFailed
from ..consts import API_URL, GATE_CA_BUNDLE, GATE_CLIENT_CERT


def get_canary_id(name, application=None):
    """Finds a canary config ID matching the name passed.
    Assumes the canary name is unique and the first match wins.
    Args:
        application (str): Name of Spinnaker Application to search (optional)
        name (str): Name of CanaryConfig to get the ID for

    Returns:
        str: ID of specified CanaryConfig.
        None: CanaryConfig not found
    """
    url = "{}/v2/canaryConfig".format(API_URL)
    canary_response = requests.get(url, verify=GATE_CA_BUNDLE, cert=GATE_CLIENT_CERT)

    if not canary_response.ok:
        raise SpinnakerPipelineCreationFailed('Could not resolve canary config id for {0}: {1}'
                                              .format(name, canary_response.json()))

    canary_options = canary_response.json()
    names = []
    for config in canary_options:
        names.append(config['name'])
        # If this canary name matches and they did not specificy the owning application
        if config['name'] == name and application is None:
            return config['id']
        # If this canary name matches and the application is listed in the canary config's owners array
        if config['name'] == name and application in config['applications']:
            return config['id']

    raise SpinnakerPipelineCreationFailed(
        'Could not resolve canary config id for: {0}.  Options are: {2}'.format(name, names))
