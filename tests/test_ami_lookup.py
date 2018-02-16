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
"""Ensure AMI names can be translated."""
import base64
import json
from unittest import mock

from foremast.utils import ami_lookup


@mock.patch('foremast.utils.lookups.GITLAB_TOKEN', return_value=True)
@mock.patch('foremast.utils.lookups._get_ami_file')
def test_ami_lookup(ami_file, token):
    """AMI lookup should contact GitLab for JSON table and resolve."""
    sample_dict = {
        'base_fedora': 'ami-xxxx',
        'tomcat8': 'ami-yyyy',
    }
    sample_json = json.dumps(sample_dict)
    ami_file.return_value = sample_json
    assert ami_lookup(name='base_fedora') == 'ami-xxxx'
    assert ami_lookup(region='us-west-2') == 'ami-yyyy'


@mock.patch('foremast.utils.lookups.AMI_JSON_URL', return_value=True)
@mock.patch('foremast.utils.lookups._get_ami_json')
def test_json_lookup(ami_file, json_url):
    """AMI lookup using json url."""
    sample_dict = {
        'us-east-1': {
            'base_fedora': 'ami-xxxx',
        },
        'us-west-2': {
            'tomcat8': 'ami-yyyy',
        }
    }
    ami_file.return_value = sample_dict
    assert ami_lookup(region='us-east-1', name='base_fedora') == 'ami-xxxx'
    assert ami_lookup(region='us-west-2', name='tomcat8') == 'ami-yyyy'


def test_no_external_lookup():
    """AMI lookup should contact GitLab for JSON table and resolve."""
    assert ami_lookup(region='us-east-1', name='no_external') == 'no_external'
