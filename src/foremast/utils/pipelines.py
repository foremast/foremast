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
"""Check Pipeline name to match format."""
import logging
import requests

from ..exceptions import SpinnakerPipelineCreationFailed
from ..consts import API_URL, GATE_CA_BUNDLE, GATE_CLIENT_CERT

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

    if len(pipeline_name_prefix) != 1:
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
    url = '{host}/applications/{app}/pipelineConfigs'.format(host=API_URL, app=app)
    response = requests.get(url, verify=GATE_CA_BUNDLE, cert=GATE_CLIENT_CERT)

    assert response.ok, 'Could not retrieve Pipelines for {0}.'.format(app)

    pipelines = response.json()
    LOG.debug('Pipelines:\n%s', pipelines)

    return pipelines


def get_pipeline_id(app='', name=''):
    """Get the ID for Pipeline _name_.

    Args:
        app (str): Name of Spinnaker Application to search.
        name (str): Name of Pipeline to get ID for.

    Returns:
        str: ID of specified Pipeline.
        None: Pipeline or Spinnaker Appliation not found.

    """
    return_id = None

    pipelines = get_all_pipelines(app=app)

    for pipeline in pipelines:
        LOG.debug('ID of %(name)s: %(id)s', pipeline)

        if pipeline['name'] == name:
            return_id = pipeline['id']
            LOG.info('Pipeline %s found, ID: %s', name, return_id)
            break

    return return_id


def normalize_pipeline_name(name=''):
    """Translate unsafe characters to underscores."""
    normalized_name = name
    for bad in '\\/?%#':
        normalized_name = normalized_name.replace(bad, '_')
    return normalized_name

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
