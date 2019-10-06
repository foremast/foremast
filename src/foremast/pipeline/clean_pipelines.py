#   Foremast - Pipeline Tooling
#
#   Copyright 2018 Gogo, LLC
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

import requests

from ..consts import RUNWAY_BASE_PATH
from ..exceptions import SpinnakerPipelineCreationFailed, SpinnakerPipelineDeletionFailed
from ..utils import check_managed_pipeline, get_all_pipelines, normalize_pipeline_name
from ..utils.gate import gate_request

LOG = logging.getLogger(__name__)


def delete_pipeline(app='', pipeline_name=''):
    """Delete _pipeline_name_ from _app_."""
    safe_pipeline_name = normalize_pipeline_name(name=pipeline_name)

    LOG.warning('Deleting Pipeline: %s', safe_pipeline_name)

    uri = '/pipelines/{app}/{pipeline}'.format(app=app, pipeline=safe_pipeline_name)

    response = gate_request(method='DELETE', uri=uri)

    if not response.ok:
        LOG.debug('Delete response code: %d', response.status_code)
        if response.status_code == requests.status_codes.codes['method_not_allowed']:
            raise SpinnakerPipelineDeletionFailed('Failed to delete "{0}" from "{1}", '
                                                  'possibly invalid Pipeline name.'.format(safe_pipeline_name, app))
        LOG.debug('Pipeline missing, no delete required.')

    LOG.debug('Deleted "%s" Pipeline response:\n%s', safe_pipeline_name, response.text)

    return response.text


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
    pipelines = get_all_pipelines(app=app)
    envs = settings['pipeline']['env']

    LOG.debug('Find Regions in: %s', envs)

    regions = set()
    for env in envs:
        try:
            regions.update(settings[env]['regions'])
        except KeyError:
            error_msg = 'Missing "{}/application-master-{}.json".'.format(RUNWAY_BASE_PATH, env)
            raise SpinnakerPipelineCreationFailed(error_msg)
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
            delete_pipeline(app=app, pipeline_name=pipeline_name)

    return True
