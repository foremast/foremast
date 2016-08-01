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

"""Retrieve list of all applictations in Spinnaker"""
import logging

import murl
import requests

from ..consts import API_URL

LOG = logging.getLogger(__name__)


def get_all_apps():
    """Get a list of all applications in Spinnaker.

    Returns:
        requests.models.Response: Response from Gate containing list of all apps.
    """
    LOG.info('Retreiving list of all Spinnaker applications')
    url = murl.Url(API_URL)
    url.path = 'applications'
    response = requests.get(url.url)

    assert response.ok, 'Could not retrieve application list'

    pipelines = response.json()
    LOG.debug('All Applications:\n%s', pipelines)

    return pipelines
