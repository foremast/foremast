"""Load base config and export package constants."""
import logging
from configparser import ConfigParser
from os.path import expanduser

LOG = logging.getLogger(__name__)


def find_config():
    """Look for **foremast.cfg** in config_locations.

    Raises:
        SystemExit: No configuration file found.

    Returns:
        ConfigParser: found configuration file
    """
    config_locations = [
        './.foremast/foremast.cfg',
        expanduser('~/.foremast/foremast.cfg'),
        '/etc/foremast/foremast.cfg',
    ]
    configurations = ConfigParser()

    cfg_file = configurations.read(config_locations)

    if not cfg_file:
        raise SystemExit('No configuration found in the following locations:\n\n{0}\n'.format('\n'.join(config_locations)))

    return configurations


config = find_config()
API_URL = config['base']['gate_api_url']
GIT_URL = config['base']['git_url']
GITLAB_TOKEN = config['credentials']['gitlab_token']
SLACK_TOKEN = config['credentials']['slack_token']
DOMAIN = config['base']['domain']
ENVS = set(config['base']['envs'].split(','))
REGIONS = set(config['base']['regions'].split(','))

ASG_WHITELIST = set(config['whitelists']['asg_whitelist'].split(','))

HEADERS = {
    'accept': '*/*',
    'content-type': 'application/json',
    'user-agent': 'foremast',
}
LOGGING_FORMAT = ('%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:' '%(lineno)d - %(message)s')
