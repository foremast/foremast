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
"""Test create_pipeline functionality"""
from unittest import mock

import pytest
from foremast.pipeline import SpinnakerPipeline

TEST_FORMAT_GENERATOR = mock.Mock()
TEST_SETTINGS = {
    'dev': {
        'regions': ['us-east-1'],
        'us-east-1': {
            'app': {
                'app_description': 'Test App Demo application'
            },
            'deploy_strategy': 'highlander',
            'regions': ['us-east-1'],
        }
    },
    'pipeline': {
        'base': 'tomcat8',
        'config_commit': '',
        'deployment': 'spinnaker',
        'documentation': '',
        'env': ['dev'],
        'eureka': True,
        'image': {
            'builder': 'ebs',
            'root_volume_size': 6
        },
        'regions': ['us-east-1', 'us-west-2'],
        'type': 'ec2'
    }
}


@pytest.fixture
@mock.patch('foremast.pipeline.create_pipeline.get_properties')
@mock.patch('foremast.pipeline.create_pipeline.get_details')
@mock.patch('foremast.pipeline.create_pipeline.os')
def spinnaker_pipeline(mock_os, mock_get_details, mock_get_prop):
    """Sets up pipeline fixture object"""
    mock_get_prop.return_value = TEST_SETTINGS
    pipelineObj = SpinnakerPipeline(
        app='appgroup',
        trigger_job='a_group_app', )
    pipelineObj.generated = TEST_FORMAT_GENERATOR
    pipelineObj.app_name = 'appgroup'
    pipelineObj.group_name = 'group'
    return pipelineObj


@mock.patch('foremast.pipeline.create_pipeline.clean_pipelines')
@mock.patch.object(SpinnakerPipeline, 'render_wrapper')
@mock.patch('foremast.pipeline.create_pipeline.get_subnets')
@mock.patch('foremast.pipeline.create_pipeline.construct_pipeline_block')
@mock.patch('foremast.pipeline.create_pipeline.renumerate_stages')
@mock.patch.object(SpinnakerPipeline, 'post_pipeline')
def test_create_pipeline_ec2(mock_post, mock_renumerate, mock_construct, mock_subnets, mock_wrapper, mock_clean,
                             spinnaker_pipeline):
    """test pipeline creation if ec2 pipeline."""
    test_block_data = {
        "env": "dev",
        "generated": TEST_FORMAT_GENERATOR,
        "previous_env": None,
        "region": "us-east-1",
        "settings": spinnaker_pipeline.settings["dev"]["us-east-1"],
        "pipeline_data": spinnaker_pipeline.settings['pipeline'],
        "region_subnets": {
            'us-east-1': ['us-east-1d', 'us-east-1a', 'us-east-1e']
        }
    }
    mock_subnets.return_value = {'dev': {'us-east-1': ['us-east-1d', 'us-east-1a', 'us-east-1e']}}
    mock_construct.return_value = '{"test": "stuff"}'
    mock_wrapper.return_value = {'stages': []}
    created = spinnaker_pipeline.create_pipeline()

    mock_construct.assert_called_with(**test_block_data)
    mock_post.assert_called_with({'stages': ['test']})

    assert created == True
