#   Foremast - Pipeline Tooling
#
#   Copyright 2019 Gogo, LLC
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
import requests
from ..exceptions import SpinnakerPipelineCreationFailed
from ..consts import API_URL, GATE_CA_BUNDLE, GATE_CLIENT_CERT


class JinjaFunctions:
    """A class with functions that can be used in Jinja templates
    Currently only supported in the manual pipeline type"""
    app_name = ""

    def __init__(self, app_name):
        self.app_name = app_name

    def get_dict(self):
        """Returns a dictionary of functions based on this classes functions which can be passed to a jinja template"""
        functions = dict()
        functions["get_canary_id"] = self.get_canary_id

        return functions

    def get_canary_id(self, name):
        """Finds a canary config ID matching the name passed.
        Assumes the canary name is unique and the first match wins.
        """
        url = "{}/v2/canaryConfig".format(API_URL)
        canary_response = requests.get(url, verify=GATE_CA_BUNDLE, cert=GATE_CLIENT_CERT)

        if not canary_response.ok:
            raise SpinnakerPipelineCreationFailed('Pipeline for {0}: {1}'.format(self.app_name,
                                                                                 canary_response.json()))

        canary_options = canary_response.json()
        names = []
        for config in canary_options:
            names.append(config['name'])
            if config['name'] == name:
                return config['id']

        raise SpinnakerPipelineCreationFailed(
            'Pipeline for {0}: Could not find canary config named {1}.  Options are: {2}'
            .format(self.app_name, name, names))
    