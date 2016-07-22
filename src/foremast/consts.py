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


def validate_section(config_handle, section):
    """Warn when *section* is missing from configurations.

    Args:
        config_handle (configparser.ConfigParser): Instance of configurations.
        section (str): Name of configuration section to retrieve.

    Returns:
        configparser.SectionProxy: Configuration *section*.
    """
    setting = None
    try:
        setting = config_handle[section]
    except KeyError:
        LOG.warning('Section missing from configurations: [%s]', section)
        config_handle.add_section(section)
        setting = config_handle[section]
    return setting


def validate_key_values(section_handle, key, default=None):
    """Warn when *key* is missing from configuration *section*.

    Args:
        section_dict (dict): Key/value entries for a configuration section.
        key (str): Configuration key to look up.
        default (object): Default object to use when *key* is not found.

    Returns:
        object: ``str`` when *key* exists, otherwise *default* object.
    """
    try:
        value = section_handle[key]
    except KeyError:
        LOG.warning('[%s] missing key "%s", using %r.', section_handle.name, key, default)
        value = default
    return value


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
        LOG.warning('No configuration found in the following locations:\n\n%s\n', '\n'.join(config_locations))

    return configurations


config = find_config()

BASE_SECTION = validate_section(config, 'base')
CREDENTIALS_SECTION = validate_section(config, 'credentials')
WHITELISTS_SECTION = validate_section(config, 'whitelists')

API_URL = validate_key_values(BASE_SECTION, 'gate_api_url')
GIT_URL = validate_key_values(BASE_SECTION, 'git_url')
DOMAIN = validate_key_values(BASE_SECTION, 'domain')
ENVS = set(validate_key_values(BASE_SECTION, 'envs', default='').split(','))
REGIONS = set(validate_key_values(BASE_SECTION, 'regions', default='').split(','))

GITLAB_TOKEN = validate_key_values(CREDENTIALS_SECTION, 'gitlab_token')
SLACK_TOKEN = validate_key_values(CREDENTIALS_SECTION, 'slack_token')

ASG_WHITELIST = set(validate_key_values(WHITELISTS_SECTION, 'asg_whitelist', default='').split(','))

HEADERS = {
    'accept': '*/*',
    'content-type': 'application/json',
    'user-agent': 'foremast',
}
LOGGING_FORMAT = ('%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:' '%(lineno)d - %(message)s')
