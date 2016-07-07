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
