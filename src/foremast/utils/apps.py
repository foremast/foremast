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

"""Application related utilities"""
import logging

import gogoutils
import murl
import requests

from ..consts import API_URL, APP_FORMATS, GATE_CA_BUNDLE, GATE_CLIENT_CERT
from ..exceptions import SpinnakerAppNotFound

LOG = logging.getLogger(__name__)


def get_all_apps():
    """Get a list of all applications in Spinnaker.

    Returns:
        requests.models.Response: Response from Gate containing list of all apps.
    """
    LOG.info('Retreiving list of all Spinnaker applications')
    url = murl.Url(API_URL)
    url.path = 'applications'
    response = requests.get(url.url,
                            verify=GATE_CA_BUNDLE,
                            cert=GATE_CLIENT_CERT)

    assert response.ok, 'Could not retrieve application list'

    pipelines = response.json()
    LOG.debug('All Applications:\n%s', pipelines)

    return pipelines


def get_details(app='groupproject', env='dev'):
    """Extract details for Application.

    Args:
        app (str): Application Name
        env (str): Environment/account to get details from

    Returns:
        collections.namedtuple with _group_, _policy_, _profile_, _role_,
            _user_.
    """
    api = murl.Url(API_URL)
    api.path = 'applications/{app}'.format(app=app)

    request = requests.get(api.url,
                           verify=GATE_CA_BUNDLE,
                           cert=GATE_CLIENT_CERT)

    if not request.ok:
        raise SpinnakerAppNotFound('"{0}" not found.'.format(app))

    app_details = request.json()

    LOG.debug('App details: %s', app_details)
    group = app_details['attributes'].get('repoProjectKey')
    project = app_details['attributes'].get('repoSlug')
    generated = gogoutils.Generator(group, project, env=env,
                                    formats=APP_FORMATS)

    LOG.debug('Application details: %s', generated)
    return generated
