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

"""Clean removed Pipelines."""
import logging

import murl
import requests

from ..consts import API_URL, GATE_CLIENT_CERT, GATE_CA_BUNDLE
from ..exceptions import SpinnakerPipelineCreationFailed
from ..utils import check_managed_pipeline, get_all_pipelines

LOG = logging.getLogger(__name__)


def clean_pipelines(app='', settings=None):
    """Delete Pipelines for regions not defined in application.json files.

    For Pipelines named **app_name [region]**, _region_ will need to appear
    in at least one application.json file. All other names are assumed
    unamanaged.

    Args:
        app (str): Application name
        settings (dict): imported configuration settings

    Returns:
        True: Upon successful completion.

    Raises:
        SpinnakerPipelineCreationFailed: Missing application.json file from
        `create-configs`.
    """
    url = murl.Url(API_URL)
    pipelines = get_all_pipelines(app=app)
    envs = settings['pipeline']['env']

    LOG.debug('Find Regions in: %s', envs)

    regions = set()
    for env in envs:
        try:
            regions.update(settings[env]['regions'])
        except KeyError:
            raise SpinnakerPipelineCreationFailed(
                'Missing "runway/application-master-{0}.json".'.format(env))
    LOG.debug('Regions defined: %s', regions)

    for pipeline in pipelines:
        pipeline_name = pipeline['name']

        try:
            region = check_managed_pipeline(name=pipeline_name, app_name=app)
        except ValueError:
            LOG.info('"%s" is not managed.', pipeline_name)
            continue

        LOG.debug('Check "%s" in defined Regions.', region)

        if region not in regions:
            LOG.warning('Deleting Pipeline: %s', pipeline_name)

            url.path = 'pipelines/{app}/{pipeline}'.format(
                app=app, pipeline=pipeline_name)
            response = requests.delete(url.url,
                                       verify=GATE_CA_BUNDLE,
                                       cert=GATE_CLIENT_CERT)

            LOG.debug('Deleted "%s" Pipeline response:\n%s', pipeline_name,
                      response.text)

    return True
