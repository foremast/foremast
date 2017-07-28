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

"""Test ec2_bake_data functionality"""

import pytest
from unittest import mock

from foremast.pipeline.construct_pipeline_block import ec2_bake_data
from foremast.exceptions import SpinnakerPipelineCreationFailed

TEST_SETTINGS = {'pipeline': {
                    'image': {
                        'builder': 'ebs',
                        'root_volume_size': 10}
                    }
                }

@mock.patch('foremast.pipeline.construct_pipeline_block.ami_lookup')
@mock.patch('foremast.pipeline.construct_pipeline_block.generate_packer_filename')
def test_ec2_bake_data(mock_packer, mock_ami_lookup):
    """Test that return dict is expected values"""
    mock_ami_lookup.return_value = 'abc123'
    mock_packer.return_value = 'test'

    bake_data = ec2_bake_data(settings=TEST_SETTINGS)
    expected_data = {'ami_id': 'abc123', 'root_volume_size': 10, 'ami_template_file': 'test'}

    assert bake_data == expected_data


@mock.patch('foremast.pipeline.construct_pipeline_block.ami_lookup')
@mock.patch('foremast.pipeline.construct_pipeline_block.generate_packer_filename')
def test_ec2_bake_assert(mock_packer, mock_ami_lookup):
    """Test that exception is thrown for high image sizes"""
    setting_high_size = TEST_SETTINGS
    setting_high_size['pipeline']['image']['root_volume_size'] = 60

    with pytest.raises(SpinnakerPipelineCreationFailed):
        ec2_bake_data(settings=setting_high_size)

