#   Foremast - Pipeline Tooling
#
#   Copyright 2018 Gogo, LLC
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
import importlib.util
import json
import logging
import sys
from configparser import ConfigParser
from os import getcwd, getenv, path
from os.path import exists, expanduser, expandvars

LOG = logging.getLogger(__name__)
LOGGING_FORMAT = '%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s'
SHORT_LOGGING_FORMAT = '[%(levelname)s] %(message)s'

logging.basicConfig(format=LOGGING_FORMAT)
logging.getLogger(__package__.split('.')[0]).setLevel(logging.INFO)

GOOD_STATUSES = frozenset(('SUCCEEDED', ))
SKIP_STATUSES = frozenset(('NOT_STARTED', ))

DEFAULT_DYNAMIC_CONFIG_FILE = '{path}/config.py'.format(path=getcwd())
"""Default `config.py` file path is in the current directory.

To override, use the `FOREMAST_CONFIG_FILE` environment variable.
"""


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
    if section not in config_handle:
        LOG.info('Section missing from configurations: [%s]', section)

    try:
        value = config_handle[section][key]
    except KeyError:
        LOG.warning('[%s] missing key "%s", using %r.', section, key, default)
        value = default

    return value


def extract_formats(config_handle):
    """Get application formats.

    See :class:`gogoutils.Formats` for available options.

    Args:
        config_handle (configparser.ConfigParser): Instance of configurations.

    Returns:
        dict: Formats in ``{$format_type: $format_pattern}``.

    """
    configurations = dict(config_handle)
    formats = dict(configurations.get('formats', {}))
    return formats


def load_dynamic_config(config_file=DEFAULT_DYNAMIC_CONFIG_FILE):
    """Load and parse dynamic config"""
    dynamic_configurations = {}

    # Insert config path so we can import it
    sys.path.insert(0, path.dirname(path.abspath(config_file)))
    try:
        config_file_spec = importlib.util.spec_from_file_location("config", config_file)
        config_file_module = importlib.util.module_from_spec(config_file_spec)
        config_file_spec.loader.exec_module(config_file_module)
        dynamic_configurations = config_file_module.CONFIG
    except ImportError:
        # Provide a default if config not found
        LOG.error('ImportError: Unable to load dynamic config. Check config.py file imports!')
    except AttributeError:
        LOG.error('AttributeError: Unable to load CONFIG from %s', config_file)

    return dynamic_configurations


def find_config():
    """Look for **foremast.cfg** in config_locations or ``./config.py``.

    Raises:
        SystemExit: No configuration file found.

    Returns:
        dict: Found dynamic or static configuration.

    """
    config_locations = [
        '/etc/foremast/foremast.cfg',
        expanduser('~/.foremast/foremast.cfg'),
        './.foremast/foremast.cfg',
    ]
    configurations = ConfigParser()

    cfg_file = configurations.read(config_locations)
    dynamic_config_file = getenv('FOREMAST_CONFIG_FILE', DEFAULT_DYNAMIC_CONFIG_FILE)

    if cfg_file:
        LOG.info('Loading static configuration file.')
    elif exists(dynamic_config_file):
        LOG.info('Loading dynamic configuration file.')
        configurations = load_dynamic_config(config_file=dynamic_config_file)
    else:
        config_locations.append(dynamic_config_file)
        LOG.warning('No configuration found in the following locations:\n%s', '\n'.join(config_locations))
        LOG.warning('Using defaults...')

    return dict(configurations)


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
        result = ast.literal_eval(str(value))
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
    raw_default_groups = validate_key_values(CONFIG, 'base', config_key, default='')
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


CONFIG = find_config()

API_URL = validate_key_values(CONFIG, 'base', 'gate_api_url')
GIT_URL = validate_key_values(CONFIG, 'base', 'git_url')
DOMAIN = validate_key_values(CONFIG, 'base', 'domain', default='example.com')
ENVS = set(validate_key_values(CONFIG, 'base', 'envs', default='').split(','))
VPC_NAME = validate_key_values(CONFIG, 'base', 'vpc_name', default='vpc')
REGIONS = set(validate_key_values(CONFIG, 'base', 'regions', default='').split(','))
MANUAL_TYPES = set(
    validate_key_values(CONFIG, 'base', 'manual_types', default='manual').split(','))
ALLOWED_TYPES = set(
    validate_key_values(CONFIG, 'base', 'types', default='ec2,lambda,s3,datapipeline,rolling,cloudfunction')
    .split(','))
RUNWAY_BASE_PATH = validate_key_values(CONFIG, 'base', 'runway_base_path', default='runway')
TEMPLATES_PATH = validate_key_values(CONFIG, 'base', 'templates_path')
AMI_JSON_URL = validate_key_values(CONFIG, 'base', 'ami_json_url')
DEFAULT_RUN_AS_USER = validate_key_values(CONFIG, 'base', 'default_run_as_user', default=None)
DEFAULT_SECURITYGROUP_RULES = _generate_security_groups('default_securitygroup_rules')
DEFAULT_EC2_SECURITYGROUPS = _generate_security_groups('default_ec2_securitygroups')
DEFAULT_ELB_SECURITYGROUPS = _generate_security_groups('default_elb_securitygroups')

EC2_PIPELINE_TYPES = tuple(validate_key_values(CONFIG, 'base', 'ec2_pipeline_types', default='ec2,rolling').split(','))
"""Comma separated list of Pipeline Types to treat as EC2 deployments.

This is useful when defining custom Pipeline Types. When Pipeline Type matches,
EC2 specific data is used in deployment, such as Auto Scaling Groups and
Availability Zones.

    | *Default*: ``ec2,rolling``
    | *Required*: No
    | *Example*: ``ec2,infrastructure,propeller``
"""

SECURITYGROUP_REPLACEMENTS = _convert_string_to_native(
    validate_key_values(
        CONFIG,
        'base',
        'securitygroup_replacements',
        default='{}',
    ))
GITLAB_TOKEN = validate_key_values(CONFIG, 'credentials', 'gitlab_token')
SLACK_TOKEN = validate_key_values(CONFIG, 'credentials', 'slack_token')
GATE_AUTHENTICATION = validate_key_values(CONFIG, 'credentials', 'gate_authentication', default={})
DEFAULT_TASK_TIMEOUT = validate_key_values(CONFIG, 'task_timeouts', 'default', default=120)
TASK_TIMEOUTS = json.loads(validate_key_values(CONFIG, 'task_timeouts', 'envs', default="{}"))
ASG_WHITELIST = set(validate_key_values(CONFIG, 'whitelists', 'asg_whitelist', default='').split(','))
APP_FORMATS = extract_formats(CONFIG)
GATE_CLIENT_CERT = expandvars(expanduser(validate_key_values(CONFIG, 'base', 'gate_client_cert', default='')))
GATE_CA_BUNDLE = expandvars(expanduser(validate_key_values(CONFIG, 'base', 'gate_ca_bundle', default='')))
LINKS = _convert_string_to_native(validate_key_values(CONFIG, 'links', 'default', default='{}'))

HEADERS = {
    'accept': '*/*',
    'content-type': 'application/json',
    'user-agent': 'foremast',
}
