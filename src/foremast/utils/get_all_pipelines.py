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
