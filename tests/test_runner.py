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
"""Test validity of runner."""
import os
from unittest import mock

import pytest

from foremast.runner import ForemastRunner
from foremast.pipeline import SpinnakerPipeline

CONFIGS = {
    'pipeline': {
        'type': None,
    },
}

ENV_VARIABLES = {
    'EMAIL': 'test@localhost.localdomain',
    'ENV': 'dev',
    'PROJECT': 'group1',
    'GIT_REPO': 'repo1',
    'REGION': 'us-east-1',
    'RUNWAY_DIR': '.',
}

for name, value in ENV_VARIABLES.items():
    os.environ[name] = value


def test_runner_create_pipeline_invalid_type():
    """Test invalid pipeline types."""
    runner = ForemastRunner()
    runner.configs = CONFIGS
    with pytest.raises(NotImplementedError):
        runner.configs['pipeline']['type'] = 'not_allowed_type'
        runner.create_pipeline()


@mock.patch('foremast.runner.consts.ALLOWED_TYPES', new=['manual'])
@mock.patch('foremast.runner.pipeline')
def test_runner_create_pipeline_onetime(mock_pipelines):
    """Test onetime pipeline."""
    runner = ForemastRunner()
    runner.configs = CONFIGS
    runner.configs['pipeline']['type'] = 'manual'
    runner.create_pipeline(onetime=True)
