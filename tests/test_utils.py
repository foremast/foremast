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

"""Test utils."""

import pytest
from unittest import mock
from foremast.utils import *
from foremast.exceptions import *

@mock.patch('foremast.utils.banners.LOG')
def test_utils_banner(mock_log):
    banner('test', border='+', width=10)
    mock_log.info.assert_called_with('+' * 10)


def test_utils_deep_chain_map():

    first = {'key1': {
            'subkey1': 1,
        },
    }
    second = {'key1': {
            'subkey2': 2,
        },
     }

    result = {'key1': {
            'subkey1': 1,
            'subkey2': 2,
        }
     }

    assert DeepChainMap(first, second) == result
    with pytest.raises(KeyError):
        assert DeepChainMap(first, second)['key2'] == result


def test_utils_pipeline_check_managed():

    assert check_managed_pipeline('app [onetime]', 'app') == 'onetime'
    assert check_managed_pipeline('app [us-east-1]', 'app') == 'us-east-1'

    params = (
        # pipeline, app, result
        ['app', 'app', 'app'],  # no region
        ['app app [us-east-1]', 'app', 'us-east-1'],  # no app
        ['app [us-east-1]', 'example', 'us-east-1'],  # app / pipeline not matching
    )
    for param in params:
        with pytest.raises(ValueError):
            assert check_managed_pipeline(param[0], param[1]) == param[2]


@mock.patch('requests.get')
@mock.patch('foremast.utils.pipelines.murl')
def test_utils_get_all_pipelines(mock_murl, mock_requests_get):
    mock_requests_get.return_value.json.return_value = {}
    result = get_all_pipelines(app='app')
    assert result == {}


@mock.patch('foremast.utils.pipelines.get_all_pipelines')
def test_utils_get_pipeline_id(mock_get_pipelines):

    data = [
        {'name': 'app', 'id': 100},
    ]
    mock_get_pipelines.return_value = data

    result = get_pipeline_id(name='app')
    assert result is 100

    result = get_pipeline_id(name='badapp')
    assert result == None


def test_utils_generate_packer_filename():
    a = generate_packer_filename('aws', 'us-east-1', 'chroot')
    assert a == 'aws_us-east-1_chroot.json'


@mock.patch('requests.get')
def test_utils_find_elb(requests_get_mock):
    results = [
        {'account': 'dev', 'region': 'us-east-1', 'dnsname': 'appdns' }
    ]
    requests_get_mock.return_value.json.return_value = results
    a = find_elb('app', 'dev', 'us-east-1')
    assert a == 'appdns'

    with pytest.raises(SpinnakerElbNotFound):
        # we already filter by app, so sending incorrect env/region combo
        # will trigger the error
        find_elb('app', 'devbad', 'us-east-1')


@mock.patch('foremast.utils.slack.slacker')
def test_utils_post_slack_message(mock_slack):
    post_slack_message('test', '#test')
    mock_slack.called


@mock.patch('requests.get')
@mock.patch('foremast.utils.pipelines.murl')
def test_utils_apps_get_details(mock_murl, mock_requests_get):
    data = {
        'attributes': {
            'repoProjectKey': 'group',
            'repoSlug': 'repo1'
        }
    }
    mock_requests_get.return_value.json.return_value = data

    result = get_details(app='repo1group', env='dev')
    assert result.app_name() == 'repo1group'

    with pytest.raises(SpinnakerAppNotFound):
        mock_requests_get.return_value.ok = False
        result = get_details(app='repo1group', env='dev')
        assert result.app_name() == 'repo1group'


@mock.patch('requests.get')
@mock.patch('foremast.utils.pipelines.murl')
def test_utils_apps_get_all_apps(mock_murl, mock_requests_get):
    data = []
    mock_requests_get.return_value.json.return_value = data

    result = get_all_apps()
    assert result == []

    with pytest.raises(AssertionError):
        mock_requests_get.return_value.ok = False
        result = get_all_apps()
