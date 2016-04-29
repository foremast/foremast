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
