#   Foremast - Pipeline Tooling
#
#   Copyright 2016 Gogo, LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""Load base config and export package constants.

The ``foremast`` configuration file is read from the following locations in
descending order. First found wins.

* ``./.foremast/foremast.cfg``
* ``~/.foremast/foremast.cfg``
* ``/etc/foremast/foremast.cfg``

.. literalinclude:: ../../src/foremast/templates/configs/foremast.cfg.example
   :language: ini
"""
import ast
import json
import logging
import sys

from configparser import ConfigParser, DuplicateSectionError
from os.path import expanduser, expandvars, exists
from os import getcwd, path

LOG = logging.getLogger(__name__)
LOGGING_FORMAT = '%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s'
SHORT_LOGGING_FORMAT = '[%(levelname)s] %(message)s'

logging.basicConfig(format=LOGGING_FORMAT)
logging.getLogger(__package__.split('.')[0]).setLevel(logging.INFO)


def validate_key_values(config_handle, section, key, default=None):
    """Warn when *key* is missing from configuration *section*.

    Args:
        config_handle (configparser.ConfigParser): Instance of configurations.
        section (str): Name of configuration section to retrieve.
        key (str): Configuration key to look up.
        default (object): Default object to use when *key* is not found.

    Returns:
        object: ``str`` when *key* exists, otherwise *default* object.
    """
    try:
        config_handle.add_section(section)
        LOG.info('Section missing from configurations: [%s]', section)
    except DuplicateSectionError:
        pass

    section_handle = config[section]

    try:
        value = section_handle[key]
    except KeyError:
        LOG.warning('[%s] missing key "%s", using %r.', section_handle.name, key, default)
        value = default

    return value


def extract_formats(config_handle):
    """Get application formats.

    Args:
        config_handle (configparser.ConfigParser): Instance of configurations.

    Returns:
        object: ``str`` when *key* exists, otherwise *default* object.
        dict: of formats in {$format_type: $format_pattern}.
        See (gogoutils.Formats) for available options.
    """
    formats = {}

    if config_handle.has_section('formats'):
        formats = dict(config_handle['formats'])

    return formats


def load_dynamic_config(configurations, config_dir=getcwd()):
    """Load and parse dynamic config"""
    # Create full path of config
    config_file = '{path}/config.py'.format(path=config_dir)

    # Insert config path so we can import it
    sys.path.insert(0, path.dirname(path.abspath(config_file)))
    try:
        config_module = __import__('config')

        for key, value in config_module.CONFIG.items():
            LOG.debug('Importing %s with key %s', key, value)
            # Update configparser object
            configurations.update({key: value})
    except ImportError:
        # Provide a default if config not found
        configurations = {}


def find_config():
    """Look for **foremast.cfg** in config_locations.

    Raises:
        SystemExit: No configuration file found.

    Returns:
        ConfigParser: found configuration file
    """
    config_locations = [
        '/etc/foremast/foremast.cfg',
        expanduser('~/.foremast/foremast.cfg'),
        './.foremast/foremast.cfg',
    ]
    configurations = ConfigParser()

    cfg_file = configurations.read(config_locations)
    dynamic_config_file = '{path}/config.py'.format(path=getcwd())

    if cfg_file:
        LOG.info('Loading static configuration file.')
    elif exists(dynamic_config_file):
        LOG.info('Loading dynamic configuration file.')
        load_dynamic_config(configurations)
    else:
        config_locations.append(dynamic_config_file)
        LOG.warning('No configuration found in the following locations:\n%s', '\n'.join(config_locations))
        LOG.warning('Using defaults...')

    return configurations


def _remove_empty_entries(entries):
    """Remove empty entries in a list"""
    valid_entries = []
    for entry in set(entries):
        if entry:
            valid_entries.append(entry)
    return sorted(valid_entries)


def _convert_string_to_native(value):
    """Convert a string to its native python type"""
    result = None

    try:
        result = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        # Likely a string
        result = value.split(',')
    return result


def _generate_security_groups(config_key):
    """Read config file and generate security group dict by environment.

    Args:
        config_key (str): Configuration file key

    Returns:
        dict: of environments in {'env1': ['group1', 'group2']} format
    """
    raw_default_groups = validate_key_values(config, 'base', config_key, default='')
    default_groups = _convert_string_to_native(raw_default_groups)
    LOG.debug('Default security group for %s is %s', config_key, default_groups)

    entries = {}
    for env in ENVS:
        entries[env] = []

    if isinstance(default_groups, (list)):
        groups = _remove_empty_entries(default_groups)
        for env in entries:
            entries[env] = groups
    elif isinstance(default_groups, (dict)):
        entries.update(default_groups)

    LOG.debug('Generated security group: %s', entries)
    return entries

config = find_config()

API_URL = validate_key_values(config, 'base', 'gate_api_url')
GIT_URL = validate_key_values(config, 'base', 'git_url')
DOMAIN = validate_key_values(config, 'base', 'domain', default='example.com')
ENVS = set(validate_key_values(config, 'base', 'envs', default='').split(','))
REGIONS = set(validate_key_values(config, 'base', 'regions', default='').split(','))
ALLOWED_TYPES = set(validate_key_values(config, 'base', 'types', default='ec2,lambda,s3,datapipeline').split(','))
TEMPLATES_PATH = validate_key_values(config, 'base', 'templates_path')
AMI_JSON_URL = validate_key_values(config, 'base', 'ami_json_url')
DEFAULT_EC2_SECURITYGROUPS = _generate_security_groups('default_ec2_securitygroups')
DEFAULT_ELB_SECURITYGROUPS = _generate_security_groups('default_elb_securitygroups')
GITLAB_TOKEN = validate_key_values(config, 'credentials', 'gitlab_token')
SLACK_TOKEN = validate_key_values(config, 'credentials', 'slack_token')
DEFAULT_TASK_TIMEOUT = validate_key_values(config, 'task_timeouts', 'default', default=120)
TASK_TIMEOUTS = json.loads(validate_key_values(config, 'task_timeouts', 'envs', default="{}"))
ASG_WHITELIST = set(validate_key_values(config, 'whitelists', 'asg_whitelist', default='').split(','))
APP_FORMATS = extract_formats(config)
GATE_CLIENT_CERT = expandvars(expanduser(validate_key_values(config, 'base', 'gate_client_cert', default='')))
GATE_CA_BUNDLE = expandvars(expanduser(validate_key_values(config, 'base', 'gate_ca_bundle', default='')))

HEADERS = {
    'accept': '*/*',
    'content-type': 'application/json',
    'user-agent': 'foremast',
}
