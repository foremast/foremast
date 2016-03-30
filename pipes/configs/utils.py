import configparser
import logging
import os

LOG = logging.getLogger(__name__)


def get_configs(file_name='spinnaker.conf'):
    """Get main configuration.

    Args:
        file_name (str): Name of configuration file to retrieve.

    Returns:
        configparser.ConfigParser object with configuration loaded.
    """
    here = os.path.dirname(os.path.realpath(__file__))
    configpath = '{0}/../../configs/{1}'.format(here, file_name)
    config = configparser.ConfigParser()
    config.read(configpath)

    LOG.debug('Configuration sections found: %s', config.sections())
    return config
