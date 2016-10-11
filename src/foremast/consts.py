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

.. literalinclude:: ../src/foremast/templates/configs/foremast.cfg.example
   :language: ini
"""
import logging
from configparser import ConfigParser, DuplicateSectionError
from os.path import expanduser, expandvars

LOG = logging.getLogger(__name__)


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
        LOG.warning('Section missing from configurations: [%s]', section)
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

    if not cfg_file:
        LOG.warning('No configuration found in the following locations:\n\n%s\n', '\n'.join(config_locations))

    return configurations


config = find_config()

API_URL = validate_key_values(config, 'base', 'gate_api_url')
GIT_URL = validate_key_values(config, 'base', 'git_url')
DOMAIN = validate_key_values(config, 'base', 'domain', default='example.com')
ENVS = set(validate_key_values(config, 'base', 'envs', default='').split(','))
REGIONS = set(validate_key_values(config, 'base', 'regions', default='').split(','))
ALLOWED_TYPES = set(validate_key_values(config, 'base', 'types', default='ec2,lambda').split(','))
TEMPLATES_PATH = validate_key_values(config, 'base', 'templates_path')
AMI_JSON_URL = validate_key_values(config, 'base', 'ami_json_url')
DEFAULT_EC2_SECURITYGROUPS = set(validate_key_values(config, 'base', 'default_ec2_securitygroups',
                                 default='').split(','))
DEFAULT_ELB_SECURITYGROUPS = set(validate_key_values(config, 'base', 'default_elb_securitygroups',
                                 default='').split(','))
GITLAB_TOKEN = validate_key_values(config, 'credentials', 'gitlab_token')
SLACK_TOKEN = validate_key_values(config, 'credentials', 'slack_token')

ASG_WHITELIST = set(validate_key_values(config, 'whitelists', 'asg_whitelist', default='').split(','))
APP_FORMATS = extract_formats(config)
GATE_CLIENT_CERT = expandvars(expanduser(validate_key_values(config, 'base', 'gate_client_cert', default='')))
GATE_CA_BUNDLE = expandvars(expanduser(validate_key_values(config, 'base', 'gate_ca_bundle', default='')))

HEADERS = {
    'accept': '*/*',
    'content-type': 'application/json',
    'user-agent': 'foremast',
}
LOGGING_FORMAT = '%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s'
