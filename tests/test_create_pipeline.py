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

import pytest

from foremast.utils import check_managed_pipeline


def test_pipeline_names():
    """Only manage names matching **app_name [region]**."""
    app_name = 'unicornforrest'

    bad_names = [
        'something',
        app_name,
        'something [us-east-1',
        'something us-east-1]',
        '{0} [us-east-1'.format(app_name),
        '{0} us-east-1]'.format(app_name),
        'some some',
        'something [us-east-1]',
        'some some [us-east-1]',
        ]

    for name in bad_names:
        with pytest.raises(ValueError):
            check_managed_pipeline(name=name, app_name=app_name)

    assert 'us-east-1' == check_managed_pipeline(
        name='{0} [us-east-1]'.format(app_name),
        app_name=app_name)
