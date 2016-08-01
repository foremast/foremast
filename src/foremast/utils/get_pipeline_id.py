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

"""Retrieve ID of Spinnaker Pipeline."""
import logging

from .get_all_pipelines import get_all_pipelines

LOG = logging.getLogger(__name__)


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
