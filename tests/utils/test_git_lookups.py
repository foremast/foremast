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
from unittest import mock

from foremast.utils import GitLookup


@mock.patch('foremast.utils.lookups.gitlab')
def test_init(gitlab):
    """Check init."""
    my_git = GitLookup()

    assert my_git.git_short == ''
    assert my_git.server == gitlab.Gitlab.return_value
    my_git.server.getproject.assert_called_with(my_git.git_short)
