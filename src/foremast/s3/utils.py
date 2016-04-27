import configparser
import logging
import os

import gogoutils
import murl
import requests

LOG = logging.getLogger(__name__)


def get_configs(file_name='spinnaker.conf'):
    """Get main configuration.

    Args:
        file_name (str): Name of configuration file to retrieve.

    Returns:
        configparser.ConfigParser object with configuration loaded.
    """
    here = os.path.dirname(os.path.realpath(__file__))
    configpath = '{0}/../configurations/{1}'.format(here, file_name)
    config = configparser.ConfigParser()
    config.read(configpath)

    LOG.debug('Configuration sections found: %s', config.sections())
    return config


def get_details(app='groupproject', env='dev'):
    """Extract details for Application.

    Returns:
        gogoutils.Generator object.
    """
    api_url = get_configs()['spinnaker']['gate_url']
    api = murl.Url(api_url)
    api.path = 'applications/{app}'.format(app=app)

    app_details = requests.get(api.url).json()

    group = app_details['attributes'].get('repoProjectKey')
    project = app_details['attributes'].get('repoSlug')
    generated = gogoutils.Generator(group, project, env=env)

    LOG.debug('Application details: %s', generated.archaius())
    return generated
