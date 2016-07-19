"""Load base config and export package constants.

The ``foremast`` configuration file is read from the following locations in
descending order. First found wins.

* ``./.foremast/foremast.cfg``
* ``~/.foremast/foremast.cfg``
* ``/etc/foremast/foremast.cfg``

.. literalinclude:: .foremast/foremast.cfg
   :language: ini
"""
import logging
from configparser import ConfigParser
from os.path import expanduser

LOG = logging.getLogger(__name__)

MISSING_KEY_MSG_FMT = 'Missing {key} from [{section}]'


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
        raise SystemExit('No configuration found in the following locations:\n\n'
                         '{0}\n'.format('\n'.join(config_locations)))

    return configurations


config = find_config()

try:
    BASE_SECTION = config['base']
    CREDENTIALS_SECTION = config['credentials']
    WHITELISTS_SECTION = config['whitelists']
except KeyError as missing_section:
    raise SystemExit('Section missing from configurations: [{0}]'.format(missing_section))

try:
    API_URL = BASE_SECTION.get('gate_api_url')
    GIT_URL = BASE_SECTION.get('git_url')
    DOMAIN = BASE_SECTION.get('domain')
    ENVS = set(BASE_SECTION.get('envs').split(','))
    REGIONS = set(BASE_SECTION.get('regions').split(','))
except KeyError as missing_base_key:
    raise SystemExit(MISSING_KEY_MSG_FMT.format(key=missing_base_key, section=BASE_SECTION.name))

try:
    GITLAB_TOKEN = CREDENTIALS_SECTION.get('gitlab_token')
    SLACK_TOKEN = CREDENTIALS_SECTION.get('slack_token')
except KeyError as missing_credentials_key:
    raise SystemExit(MISSING_KEY_MSG_FMT.format(key=missing_credentials_key, section=CREDENTIALS_SECTION.name))

try:
    ASG_WHITELIST = set(WHITELISTS_SECTION.get('asg_whitelist').split(','))
except KeyError as missing_whitelists_key:
    raise SystemExit(MISSING_KEY_MSG_FMT.format(key=missing_whitelists_key, section=WHITELISTS_SECTION.name))

HEADERS = {
    'accept': '*/*',
    'content-type': 'application/json',
    'user-agent': 'foremast',
}
LOGGING_FORMAT = ('%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:' '%(lineno)d - %(message)s')
