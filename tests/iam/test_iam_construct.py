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
"""Test IAM Policies for correctness."""
import copy
import json
from unittest import mock

from foremast.iam.construct_policy import construct_policy
from foremast.utils.templates import get_template

BASE_SETTINGS = json.loads(get_template(template_file='configs/pipeline.json.j2'))


@mock.patch('foremast.utils.credentials.API_URL', 'http://test.com')
@mock.patch('foremast.utils.credentials.requests.get')
def test_iam_construct_policy(requests_get):
    """Check general assemblage."""
    settings = copy.deepcopy(BASE_SETTINGS)

    policy_json = construct_policy(pipeline_settings=settings)
    # checking empty policy
    assert policy_json is None

    settings.update({'services': {'s3': True}})
    policy_json = construct_policy(app='unicornforrest', env='stage', group='forrest', pipeline_settings=settings)

    # checking s3 policy
    assert type(json.loads(policy_json)) == dict

    # TODO: Test other services besides S3
    settings.update({'services': {'dynamodb': ['coreforrest', 'edgeforrest', 'attendantdevops']}})
    policy_json = construct_policy(pipeline_settings=settings)
    policy = json.loads(policy_json)


@mock.patch('foremast.utils.credentials.API_URL', 'http://test.com')
@mock.patch('foremast.utils.credentials.requests.get')
def test_construct_cloudwatchlogs(requests_get):
    """Check Lambda Policy."""
    pipeline_settings = copy.deepcopy(BASE_SETTINGS)
    pipeline_settings.update({'services': {'cloudwatchlogs': True}, 'type': 'lambda'})

    policy_json = construct_policy(
        app='unicornforrest', env='dev', group='forrest', pipeline_settings=pipeline_settings)
    policy = json.loads(policy_json)

    statements = list(statement for statement in policy['Statement'] if statement['Sid'] == 'LambdaCloudWatchLogs')
    assert len(statements) == 1

    statement = statements[0]
    assert statement['Effect'] == 'Allow'
    assert len(statement['Action']) == 3
    assert all(action.startswith('logs:') for action in statement['Action'])


@mock.patch('foremast.utils.credentials.API_URL', 'http://test.com')
@mock.patch('foremast.utils.credentials.requests.get')
def test_construct_s3(requests_get):
    """Check S3 Policy."""
    pipeline_settings = copy.deepcopy(BASE_SETTINGS)
    pipeline_settings.update({'services': {'s3': True}})

    construct_policy_kwargs = {'app': 'unicornforrest',
                               'env': 'dev',
                               'group': 'forrest',
                               'pipeline_settings': pipeline_settings}

    policy_json = construct_policy(**construct_policy_kwargs)
    policy = json.loads(policy_json)
    assert len(policy['Statement']) == 2

    allow_list_policy, allow_edit_policy = policy['Statement']

    assert len(allow_list_policy['Action']) == 1
    assert 's3:ListBucket' in allow_list_policy['Action']
    assert len(allow_list_policy['Resource']) == 1

    assert len(allow_edit_policy['Action']) == 3
    assert all(('s3:{0}Object'.format(action) in allow_edit_policy['Action'] for action in ('Delete', 'Get', 'Put')))
    assert len(allow_edit_policy['Resource']) == 1


@mock.patch('foremast.utils.credentials.API_URL', 'http://test.com')
@mock.patch('foremast.utils.credentials.requests.get')
def test_construct_s3_buckets(requests_get):
    """Check S3 Policy with multiple Buckets listed."""
    pipeline_settings = copy.deepcopy(BASE_SETTINGS)
    pipeline_settings.update({'services': {'s3': ['Bucket1', 'Bucket2']}})

    construct_policy_kwargs = {'app': 'unicornforrest',
                               'env': 'dev',
                               'group': 'forrest',
                               'pipeline_settings': pipeline_settings}

    policy_json = construct_policy(**construct_policy_kwargs)
    policy = json.loads(policy_json)
    print(policy)
    assert len(policy['Statement']) == 2

    allow_list_policy, allow_edit_policy = policy['Statement']

    assert len(allow_list_policy['Resource']) == 3

    assert len(allow_edit_policy['Resource']) == 3
