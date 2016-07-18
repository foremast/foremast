"""Package constants."""
from configparser import ConfigParser
import logging
from os.path import expanduser

LOG = logging.getLogger(__name__)



def find_config():
    """Looks for config in CONFIG_LOCATIONS. If not found, gives a fatal error

    Returns:
        ConfigParser: found configuration file
    """
    config_locations = [
        './.foremast/foremast.cfg',
        expanduser('~/.foremast/foremast.cfg'),
        '/etc/foremast/foremast.cfg',
        ]
    config = ConfigParser()

    cfg_file = config.read(config_locations)

    if not cfg_file:
        LOG.error('No config found in the following locations: {0}\n'.format(CONFIG_LOCATIONS))

    return config


def get_configs(config, section=''):
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
    if config[section]:
        return dict(config[section])
    else:
        raise KeyError('Section "{0}" missing from configuraton file.'.format(section))


#Load in consts from config
config = find_config()
API_URL = config['urls']['gate_api_url']
GIT_URL = config['urls']['git_url']
GITLAB_TOKEN = config['credentials']['gitlab_token']
SLACK_TOKEN = get_configs(config, section='credentials')['slack_token']

HEADERS = {
    'accept': '*/*',
    'content-type': 'application/json',
    'user-agent': 'foremast',
}
LOGGING_FORMAT = ('%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:'
                  '%(lineno)d - %(message)s')

DOMAIN = 'example.com'
ENVS = set(('build', 'dev', 'stage', 'prod', 'prods', 'prodp'))
REGIONS = set(('us-east-1', 'us-west-2'))

ASG_WHITELIST = [
    'profileservicecoreapis'
]


