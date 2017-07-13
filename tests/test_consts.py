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

from configparser import ConfigParser
from unittest.mock import patch

from foremast.consts import ALLOWED_TYPES, extract_formats, _generate_security_groups


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


@patch('foremast.consts.validate_key_values')
def test_parse_security_group(values):
    """Parse out security group entries"""
    values.return_value = 'g1'
    assert {'': ['g1']} == _generate_security_groups('default_ec2_securitygroups')

    values.return_value = 'g1,g2'
    assert {'': ['g1', 'g2']} == _generate_security_groups('default_ec2_securitygroups')

    values.return_value = {'dev': ['g1', 'g2'], 'stage': ['g3']}
    assert {'dev': ['g1', 'g2'], 'stage': ['g3']} == _generate_security_groups('default_ec2_securitygroups')
