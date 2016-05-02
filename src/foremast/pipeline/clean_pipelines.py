"""Clean removed Pipelines."""
import logging

import murl
import requests

from ..consts import API_URL
from ..utils import check_managed_pipeline, get_all_pipelines

LOG = logging.getLogger(__name__)


def clean_pipelines(app='', settings=None):
    """Delete Pipelines for regions not defined in application.json files.

    For Pipelines named **app_name [region]**, _region_ will need to appear
    in at least one application.json file. All other names are assumed
    unamanaged.

    Returns:
        True: Upon successful completion.
    """
    url = murl.Url(API_URL)
    pipelines = get_all_pipelines(app=app)
    envs = settings['pipeline']['env']

    LOG.debug('Find Regions in: %s', envs)

    regions = set()
    for env in envs:
        regions.update(settings[env]['regions'])
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
            response = requests.delete(url.url)

            LOG.debug('Deleted "%s" Pipeline response:\n%s', pipeline_name,
                      response.text)

    return True
