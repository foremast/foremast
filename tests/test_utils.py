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

    bad_names = [
        'something',
        'app',
        'app [us-east-1',
        'app us-east-1]',
        'app [us-east-1',
        'app us-east-1]',
        'app name',
        'app2 [us-east-1]',
        'app name [us-east-1]',
        ]

    for name in bad_names:
        with pytest.raises(ValueError):
            check_managed_pipeline(name=name, app_name='app')


@mock.patch('requests.get')
@mock.patch('foremast.utils.pipelines.murl')
def test_utils_pipeline_get_all_pipelines(mock_murl, mock_requests_get):
    mock_requests_get.return_value.json.return_value = {}
    result = get_all_pipelines(app='app')
    assert result == {}


@mock.patch('foremast.utils.pipelines.get_all_pipelines')
def test_utils_pipeline_get_pipeline_id(mock_get_pipelines):

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
@mock.patch('foremast.utils.apps.API_URL', 'http://test.com')
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
@mock.patch('foremast.utils.apps.API_URL', 'http://test.com')
def test_utils_apps_get_all_apps(mock_murl, mock_requests_get):
    data = []
    mock_requests_get.return_value.json.return_value = data

    result = get_all_apps()
    assert result == []

    with pytest.raises(AssertionError):
        mock_requests_get.return_value.ok = False
        result = get_all_apps()


@mock.patch('foremast.utils.dns.boto3.Session')
@mock.patch('foremast.utils.dns.DOMAIN', 'test')
def test_utils_dns_get_zone_ids(mock_boto3):
    data = {
        'HostedZones': [
                {'Name': 'internal.example.com', 'Id': 100, 'Config': {'PrivateZone': True}},
                {'Name': 'external.example.com', 'Id': 101, 'Config': {'PrivateZone': False}},
            ]
    }

    data_external = {
        'HostedZones': [
                {'Name': 'internal.example.com', 'Id': 100, 'Config': {'PrivateZone': False}},
                {'Name': 'external.example.com', 'Id': 101, 'Config': {'PrivateZone': False}},
            ]
    }

    mock_boto3.return_value.client.return_value.list_hosted_zones_by_name.return_value = data

    # default case
    result = get_dns_zone_ids()
    assert result == [100]

    # all zones
    result = get_dns_zone_ids(facing='external')
    assert result == [100, 101]

    # all internal
    result = get_dns_zone_ids(facing='internal')
    assert result == [100]

    # no internal zones
    mock_boto3.return_value.list_hosted_zones_by_name.return_value = data_external
    result = get_dns_zone_ids(facing='internal')
    assert result == []


@mock.patch('requests.get')
@mock.patch('foremast.utils.security_group.get_vpc_id')
def test_utils_sg_get_security_group_id(mock_vpc_id, mock_requests_get):
    data = {'id': 100}
    mock_requests_get.return_value.json.return_value = data

    # default - happy path
    result = get_security_group_id()
    assert result == 100

    # security group not found
    with pytest.raises(SpinnakerSecurityGroupError):
        mock_requests_get.return_value.json.return_value = {}
        result = get_security_group_id()

    # error getting details
    with pytest.raises(AssertionError):
        mock_requests_get.return_value.ok = False
        result = get_security_group_id()


@mock.patch('requests.get')
def test_utils_vpc_get_vpc_id(mock_requests_get):
    data = [
        {'id': 100, 'name': 'vpc','account': 'dev', 'region': 'us-east-1'},
    ]
    mock_requests_get.return_value.json.return_value = data

    # default - happy path
    result = get_vpc_id(account='dev', region='us-east-1')
    assert result == 100

    # vpc not found
    with pytest.raises(SpinnakerVPCIDNotFound):
        result = get_vpc_id(account='dev', region='us-west-2')
        assert result == 100

    # error getting details
    with pytest.raises(SpinnakerVPCNotFound):
        mock_requests_get.return_value.ok = False
        result = get_vpc_id(account='dev', region='us-east-1')


@mock.patch('foremast.utils.subnets.requests.get')
def test_utils_subnets_get_subnets(mock_requests_get):
    data = [
        {'vpcId': 100, 'account': 'dev', 'region': 'us-east-1',
         'target': 'ec2', 'availabilityZone': []},
        {'vpcId': 101, 'account': 'dev', 'region': 'us-west-2',
         'target': 'ec2', 'availabilityZone': ['us-west-2a', 'us-west-2b']},
    ]

    mock_requests_get.return_value.json.return_value = data

    # default - happy path
    result = get_subnets(env='dev', region='us-east-1')
    assert result == {'us-east-1': [[]]}

    # default - happy path w/multiple az
    result = get_subnets(env='dev', region='')
    assert result == {'dev': {'us-west-2': [['us-west-2a', 'us-west-2b']], 'us-east-1': [[]]}}

    # subnet not found
    with pytest.raises(SpinnakerSubnetError):
        result = get_subnets(env='dev', region='us-west-1')
        assert result == {'us-west-1': [[]]}

    # error getting details
    with pytest.raises(SpinnakerTimeout):
        mock_requests_get.return_value.ok = False
        result = get_subnets()
