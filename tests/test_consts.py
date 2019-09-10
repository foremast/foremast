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

from configparser import ConfigParser
from unittest.mock import patch

from foremast.consts import (ALLOWED_TYPES, DEFAULT_SECURITYGROUP_RULES, EC2_PIPELINE_TYPES, RUNWAY_BASE_PATH,
                             _generate_security_groups, extract_formats, validate_key_values)


def test_consts_extract_formats():
    """Test extract_formats()"""

    format_defaults = {
        'domain': 'example.com',
        'app': '{project}',
    }

    config = ConfigParser(defaults=format_defaults)
    config.add_section('formats')

    results = extract_formats(config)
    assert 'example.com' == results['domain']


def test_consts_pipeline_types():
    """Default types should be set."""
    assert 'ec2' in ALLOWED_TYPES
    assert 'lambda' in ALLOWED_TYPES


def test_consts_default_securitygroup_rules():
    """Test this const is a dict"""
    assert isinstance(DEFAULT_SECURITYGROUP_RULES, dict)
    # assert DEFAULT_SECURITYGROUP_RULES == {} or {'': []}


@patch('foremast.consts.validate_key_values')
def test_parse_security_group(values):
    """Parse out security group entries"""
    values.return_value = 'g1'
    assert {'': ['g1']} == _generate_security_groups('default_ec2_securitygroups')

    values.return_value = 'g1,g2'
    assert {'': ['g1', 'g2']} == _generate_security_groups('default_ec2_securitygroups')


@patch('foremast.consts.validate_key_values', return_value="{'': ['g3']}")
def test_parse_security_group_dict(mock_keys):
    """Validate security groups are handled properly if dictionary is in dyanmic config"""
    assert {'': ['g3']} == _generate_security_groups('default_elb_securitygroups')


def test_parse_ec2_pipeline_types():
    """Validate EC2 Pipeline Types."""
    assert EC2_PIPELINE_TYPES == ('ec2', 'rolling')
    assert isinstance(EC2_PIPELINE_TYPES, tuple)

def test_consts_default_runway_base_path():
    """Validate default runway base path remains unchanged"""
    assert RUNWAY_BASE_PATH == 'runway'

def test_consts_custom_runway_base_path():
    """Validate custom runway base path changes as expected"""
    sample_config = {'base': {'runway_base_path': 'custom'}}
    result = validate_key_values(sample_config, 'base', 'runway_base_path', default='runway')
    assert result == 'custom'
