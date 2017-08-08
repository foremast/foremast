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


@mock.patch('foremast.utils.lookups.GITLAB_TOKEN')
@mock.patch('foremast.utils.lookups.gitlab.Gitlab')
def test_ami_lookup(gitlab, token):
    """AMI lookup should contact GitLab for JSON table and resolve."""
    sample_dict = {
        'base_fedora': 'ami-xxxx',
        'tomcat8': 'ami-xxxx',
    }
    sample_json = json.dumps(sample_dict)
    gitlab.return_value.getfile.return_value = {'content': base64.b64encode(sample_json.encode())}
    assert ami_lookup(name='base_fedora').startswith('ami-xxxx')
    assert ami_lookup(region='us-west-2').startswith('ami-xxxx')
