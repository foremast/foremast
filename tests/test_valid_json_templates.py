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
"""Test validity of json in templates"""
import json

import pytest

from foremast.exceptions import ForemastTemplateNotFound
from foremast.utils import get_template


def test_get_template():
    with pytest.raises(ForemastTemplateNotFound):
        template = get_template(template_file='doesnotexist.json.j2')


def valid_json(template, data):
    parsed_template = get_template(template_file=template, data=data)

    assert type(json.loads(parsed_template)) == dict


def test_valid_json_configs():

    data = {
        'env': 'dev',
        'profile': 'profile',
        'app': 'testapp',
    }

    valid_json(template='configs/configs.json.j2', data=data)


def test_valid_json_pipeline():
    data = {}
    valid_json(template='configs/pipeline.json.j2', data=data)
