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
"""Test IAM Policies for correctness."""
import copy
import json
from unittest import mock

import pytest

from foremast.iam.construct_policy import construct_policy
from foremast.utils.templates import get_template


@pytest.fixture
@mock.patch('foremast.utils.templates.TEMPLATES_PATH', None)
def get_base_settings():
    return json.loads(get_template(template_file='configs/pipeline.json.j2'))


@mock.patch('foremast.utils.credentials.gate_request')
@mock.patch('foremast.utils.templates.TEMPLATES_PATH', None)
def test_iam_construct_policy(gate_request, get_base_settings):
    """Check general assemblage."""
    settings = get_base_settings

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


@mock.patch('foremast.utils.credentials.gate_request')
@mock.patch('foremast.utils.templates.TEMPLATES_PATH', None)
def test_construct_cloudwatchlogs(gate_request, get_base_settings):
    """Check Lambda Policy."""
    pipeline_settings = get_base_settings
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


@mock.patch('foremast.utils.credentials.gate_request')
@mock.patch('foremast.utils.templates.TEMPLATES_PATH', None)
def test_construct_s3(gate_request, get_base_settings):
    """Check S3 Policy."""
    pipeline_settings = get_base_settings
    pipeline_settings.update({'services': {'s3': True}})

    construct_policy_kwargs = {
        'app': 'unicornforrest',
        'env': 'dev',
        'group': 'forrest',
        'pipeline_settings': pipeline_settings
    }

    policy_json = construct_policy(**construct_policy_kwargs)
    policy = json.loads(policy_json)
    assert len(policy['Statement']) == 2

    allow_list_policy, allow_edit_policy = policy['Statement']

    assert len(allow_list_policy['Action']) == 3
    assert 's3:ListBucket' in allow_list_policy['Action']
    assert len(allow_list_policy['Resource']) == 0

    assert len(allow_edit_policy['Action']) == 5
    assert all(('s3:{0}Object'.format(action) in allow_edit_policy['Action'] for action in ('Delete', 'Get', 'Put')))
    assert len(allow_edit_policy['Resource']) == 0


@mock.patch('foremast.utils.credentials.gate_request')
@mock.patch('foremast.utils.templates.TEMPLATES_PATH', None)
def test_construct_s3_buckets(gate_request, get_base_settings):
    """Check S3 Policy with multiple Buckets listed."""
    pipeline_settings = get_base_settings
    pipeline_settings.update({'services': {'s3': ['Bucket1', 'Bucket2']}})

    construct_policy_kwargs = {
        'app': 'unicornforrest',
        'env': 'dev',
        'group': 'forrest',
        'pipeline_settings': pipeline_settings
    }

    policy_json = construct_policy(**construct_policy_kwargs)
    policy = json.loads(policy_json)
    print(policy)
    assert len(policy['Statement']) == 2

    allow_list_policy, allow_edit_policy = policy['Statement']

    assert len(allow_list_policy['Resource']) == 2

    assert len(allow_edit_policy['Resource']) == 2


@mock.patch('foremast.utils.credentials.gate_request')
@mock.patch('foremast.utils.templates.TEMPLATES_PATH', None)
def test_construct_sdb_domains(gate_request, get_base_settings):
    """Check SimpleDB Policy with multiple Domains listed."""
    pipeline_settings = get_base_settings
    pipeline_settings.update({'services': {'sdb': ['Domain1', 'Domain2']}})

    construct_policy_kwargs = {
        'app': 'unicornforrest',
        'env': 'dev',
        'group': 'forrest',
        'pipeline_settings': pipeline_settings
    }

    policy_json = construct_policy(**construct_policy_kwargs)
    policy = json.loads(policy_json)
    assert len(policy['Statement']) == 1
    assert len(policy['Statement'][0]['Resource']) == 2
    assert policy['Statement'][0]['Resource'][0].endswith('Domain1')
    assert policy['Statement'][0]['Resource'][1].endswith('Domain2')
