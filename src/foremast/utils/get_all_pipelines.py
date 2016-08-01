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

"""Retrieve list of all Pipelines."""
import logging

import murl
import requests

from ..consts import API_URL

LOG = logging.getLogger(__name__)


def get_all_pipelines(app=''):
    """Get a list of all the Pipelines in _app_.

    Args:
        app (str): Name of Spinnaker Application.

    Returns:
        requests.models.Response: Response from Gate containing Pipelines.
    """
    url = murl.Url(API_URL)
    url.path = 'applications/{app}/pipelineConfigs'.format(app=app)
    response = requests.get(url.url)

    assert response.ok, 'Could not retrieve Pipelines for {0}.'.format(app)

    pipelines = response.json()
    LOG.debug('Pipelines:\n%s', pipelines)

    return pipelines
