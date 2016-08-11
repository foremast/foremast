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
"""Test IAM Policy construction."""
from unittest import mock

from foremast.iam.create_iam import create_iam_resources


@mock.patch('foremast.iam.create_iam.boto3.session.Session')
@mock.patch('foremast.iam.create_iam.construct_policy')
@mock.patch('foremast.iam.create_iam.get_details')
@mock.patch('foremast.iam.create_iam.get_properties')
def test_create_iam_resources(get_properties, get_details, construct_policy, session):
    """Check basic functionality."""
    get_details.return_value.iam.return_value = {'group': 1, 'policy': 2, 'profile': 3, 'role': 4, 'user': 5}
    assert create_iam_resources()
