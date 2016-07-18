"""Finds and loads foremast base configuration file"""

from configparser import ConfigParser
import logging
from os.path import expanduser

LOG = logging.getLogger(__name__)

CONFIG_LOCATIONS = [
    './.foremast/foremast.cfg',
    expanduser('~/.foremast/foremast.cfg'),
    '/etc/foremast/foremast.cfg',
]


def find_config():
    """Looks for config in CONFIG_LOCATIONS. If not found, gives a fatal error

    Returns:
        ConfigParser: found configuration file
    """
    config = ConfigParser()

    cfg_file = config.read(CONFIG_LOCATIONS)

    if not cfg_file:
        LOG.error('No config found in the following locations: {0}\n'.format(CONFIG_LOCATIONS))

    return config


def get_configs(section=''):
    """Get information for a given config _section_.

    Example:
        >>> from utils import config_loader
        >>> config = config_loader.get_config(section='section')
        >>> config['key']
        'value'

    Args:
        section (str): Configuration to find.

    Returns:
        dict: Configuration information for *section*.

    Raises:
        KeyError: _section_ missing from configuration file.
    """
    config = find_config()
    if config[section]:
        return dict(config[section])
    else:
        raise KeyError('Section "{0}" missing from configuraton file.'.format(section))

