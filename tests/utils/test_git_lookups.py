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
"""Test Git file lookups."""
import base64
from unittest import mock

import pytest
from foremast.utils import GitLookup

TEST_JSON = '''{
    "ship": "pirate"
}'''
TEST_JSON_BYTES = TEST_JSON.encode()


@mock.patch('foremast.utils.lookups.gitlab')
def test_init(gitlab):
    """Check init."""
    my_git = GitLookup()

    assert my_git.git_short == ''
    assert my_git.server == gitlab.Gitlab.return_value
    my_git.server.getproject.assert_called_with(my_git.git_short)


@mock.patch('foremast.utils.lookups.gitlab')
def test_get(gitlab):
    """Check _get_ method."""
    my_git = GitLookup()

    my_git.server.getfile.return_value = {'content': base64.b64encode(TEST_JSON_BYTES)}

    result = my_git.get()
    assert isinstance(result, str)
    assert TEST_JSON == my_git.get()


@mock.patch('foremast.utils.lookups.gitlab')
def test_json(gitlab):
    """Check _json_ method."""
    my_git = GitLookup()

    my_git.server.getfile.return_value = {'content': base64.b64encode(TEST_JSON_BYTES)}

    result = my_git.json()
    assert isinstance(result, dict)
    assert result['ship'] == 'pirate'


@mock.patch('foremast.utils.lookups.gitlab')
def test_invalid_json(gitlab):
    """Check invalid JSON."""
    my_git = GitLookup()

    my_git.server.getfile.return_value = {'content': base64.b64encode(TEST_JSON_BYTES + b'}')}

    with pytest.raises(SystemExit):
        my_git.json()
