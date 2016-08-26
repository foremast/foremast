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

"""Check Pipeline name to match format."""
import logging
import requests
import murl

from ..consts import API_URL, GATE_CLIENT_CERT, GATE_CA_BUNDLE

LOG = logging.getLogger(__name__)


def check_managed_pipeline(name='', app_name=''):
    """Check a Pipeline name is a managed format **app_name [region]**.

    Args:
        name (str): Name of Pipeline to check.
        app_name (str): Name of Application to find in Pipeline name.

    Returns:
        str: Region name from managed Pipeline name.

    Raises:
        ValueError: Pipeline is not managed.
    """
    *pipeline_name_prefix, bracket_region = name.split()
    region = bracket_region.strip('[]')

    not_managed_message = '"{0}" is not managed.'.format(name)

    if 'onetime' in region:
        LOG.info('"%s" is a onetime, marked for cleaning.', name)
        return region

    if not all([bracket_region.startswith('['), bracket_region.endswith(']')]):
        LOG.debug('"%s" does not end with "[region]".', name)
        raise ValueError(not_managed_message)

    if len(pipeline_name_prefix) is not 1:
        LOG.debug('"%s" does not only have one word before [region].', name)
        raise ValueError(not_managed_message)

    if app_name not in pipeline_name_prefix:
        LOG.debug('"%s" does not use "%s" before [region].', name, app_name)
        raise ValueError(not_managed_message)

    return region


def get_all_pipelines(app=''):
    """Get a list of all the Pipelines in _app_.

    Args:
        app (str): Name of Spinnaker Application.

    Returns:
        requests.models.Response: Response from Gate containing Pipelines.
    """
    url = murl.Url(API_URL)
    url.path = 'applications/{app}/pipelineConfigs'.format(app=app)
    response = requests.get(url.url,
                            verify=GATE_CA_BUNDLE,
                            cert=GATE_CLIENT_CERT)

    assert response.ok, 'Could not retrieve Pipelines for {0}.'.format(app)

    pipelines = response.json()
    LOG.debug('Pipelines:\n%s', pipelines)

    return pipelines


def get_pipeline_id(name=''):
    """Get the ID for Pipeline _name_.

    Args:
        name (str): Name of Pipeline to get ID for.

    Returns:
        str: ID of specified Pipeline.
        None: Pipeline or Spinnaker Appliation not found.
    """
    return_id = None

    pipelines = get_all_pipelines(name)

    for pipeline in pipelines:
        LOG.debug('ID of %(name)s: %(id)s', pipeline)

        if pipeline['name'] == name:
            return_id = pipeline['id']
            LOG.info('Pipeline %s found, ID: %s', name, return_id)
            break

    return return_id
