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
"""Test Git file lookups."""
import base64
from unittest import mock

import pytest

from foremast.exceptions import GitLabApiError
from foremast.utils import FileLookup

TEST_JSON = '''{
    "ship": "pirate"
}'''
TEST_JSON_BYTES = TEST_JSON.encode()


@mock.patch('foremast.utils.lookups.gitlab')
def test_init(gitlab):
    """Check init."""
    my_git = FileLookup()
    assert my_git.git_short == ''
    assert my_git.server == gitlab.Gitlab.return_value
    my_git.server.projects.get.assert_called_with(my_git.git_short)


@mock.patch('foremast.utils.lookups.gitlab')
def test_project_exception(mock_gitlab):
    """Check resolving GitLab Project ID fails with exception."""
    mock_gitlab.Gitlab.return_value.projects.get.return_value = False

    with pytest.raises(GitLabApiError):
        FileLookup()


@mock.patch('foremast.utils.lookups.gitlab')
def test_project_success(mock_gitlab):
    """Check resolving GitLab Project ID is successful."""
    mock_gitlab.Gitlab.return_value.projects.get.return_value = object
    seeker = FileLookup()
    assert seeker.project is object


@mock.patch.object(FileLookup, 'remote_file', return_value=TEST_JSON)
@mock.patch('foremast.utils.lookups.gitlab')
def test_get(gitlab, mock_lookup):
    """Check _get_ method."""
    my_git = FileLookup()

    result = my_git.get()
    assert isinstance(result, str)
    assert TEST_JSON == my_git.get()


@mock.patch.object(FileLookup, 'get', return_value=TEST_JSON)
@mock.patch('foremast.utils.lookups.gitlab')
def test_json(gitlab, mock_lookup):
    """Check _json_ method."""
    my_git = FileLookup()

    result = my_git.json()
    assert isinstance(result, dict)
    assert result['ship'] == 'pirate'


@mock.patch.object(FileLookup, 'get', return_value=TEST_JSON + '}')
@mock.patch('foremast.utils.lookups.gitlab')
def test_invalid_json(gitlab, mock_lookup):
    """Check invalid JSON."""
    my_git = FileLookup()

    with pytest.raises(SystemExit):
        my_git.json()


def test_filelookup_attr():
    """Make sure Git related attributes are missing when runway is specified."""
    my_git = FileLookup(runway_dir='/poop_deck')

    assert my_git.git_short == ''
    assert my_git.server is None


@mock.patch('foremast.utils.lookups.gitlab')
def test_runway_get(gitlab, tmpdir):
    """Make sure Git is not called when runway is specified."""
    filename = 'test.json'

    tmpdir.join(filename).write(TEST_JSON)

    my_git = FileLookup(runway_dir=str(tmpdir))
    result = my_git.get(filename=filename)

    assert isinstance(result, str)
    assert result == TEST_JSON

    with pytest.raises(FileNotFoundError):
        my_git.get(filename='parrot')
