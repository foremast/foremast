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
"""Ensure Security Groups get created properly"""
import json
from unittest import mock

import pytest

from foremast.exceptions import ForemastConfigurationFileError
from foremast.securitygroup import SpinnakerSecurityGroup


SAMPLE_JSON = """{"security_group": {
                    "description": "something useful",
                    "egress": "0.0.0.0/0",
                    "elb_extras": [],
                    "ingress": {
                      "coreforrest": [{
                        "start_port": 8080, "end_port": 8080,
                        "env": "dev", "protocol": "tcp"
                      }],
                      "sg_apps": [{
                        "start_port": 80, "end_port": 80, "protocol": "tcp"
                      }]
                    }
                  }}"""


@mock.patch('foremast.securitygroup.create_securitygroup.boto3')
@mock.patch('foremast.securitygroup.create_securitygroup.get_security_group_id')
@mock.patch('foremast.securitygroup.create_securitygroup.get_vpc_id')
@mock.patch('foremast.securitygroup.create_securitygroup.wait_for_task')
@mock.patch("foremast.securitygroup.create_securitygroup.get_properties")
@mock.patch("foremast.securitygroup.create_securitygroup.get_details")
def test_create_crossaccount_securitygroup(get_details, pipeline_config, wait_for_task, get_vpc_id,
                                           get_security_group_id, boto3):
    """Should create SG with cross account true"""
    pipeline_config.return_value = json.loads(SAMPLE_JSON)

    get_security_group_id.return_value = 'SGID'
    get_vpc_id.return_value = 'VPCID'

    x = SpinnakerSecurityGroup(app='edgeforrest', env='dev', region='us-east-1')
    assert x.create_security_group() is True


@mock.patch('foremast.securitygroup.create_securitygroup.get_properties')
@mock.patch("foremast.securitygroup.create_securitygroup.get_details")
def test_missing_configuration(get_details, get_properties):
    """Make missing Security Group configurations more apparent."""
    get_properties.return_value = {}

    security_group = SpinnakerSecurityGroup()

    with pytest.raises(ForemastConfigurationFileError):
        security_group.create_security_group()


@mock.patch('foremast.securitygroup.create_securitygroup.get_properties')
@mock.patch("foremast.securitygroup.create_securitygroup.get_details")
def test_misconfiguration(get_details, get_properties):
    """Make bad Security Group definitions more apparent."""
    get_properties.return_value = {'security_group': {}}

    security_group = SpinnakerSecurityGroup()

    with pytest.raises(ForemastConfigurationFileError):
        security_group.create_security_group()


@mock.patch('foremast.securitygroup.create_securitygroup.boto3')
@mock.patch('foremast.securitygroup.create_securitygroup.get_properties')
@mock.patch('foremast.securitygroup.create_securitygroup.get_security_group_id')
@mock.patch("foremast.securitygroup.create_securitygroup.get_details")
def test_tags(get_details, get_security_group_id, get_properties, boto3):
    """Make bad Security Group definitions more apparent."""
    get_properties.return_value = {'security_group': {}}
    get_security_group_id.return_value = 'SGID'

    security_group = SpinnakerSecurityGroup()
    assert security_group.add_tags() is True


@mock.patch('foremast.securitygroup.create_securitygroup.get_details')
@mock.patch('foremast.securitygroup.create_securitygroup.get_properties')
def test_default_security_groups(mock_properties, mock_details):
    """Make sure default Security Groups are added to the ingress rules."""
    ingress = {
        'test_app': [
            {
                'start_port': 30,
                'end_port': 30,
            },
        ],
    }

    mock_properties.return_value = {
        'security_group': {
            'ingress': ingress,
            'description': '',
        },
    }

    test_sg = {
        'myapp': [
            {
                'start_port': '22',
                'end_port': '22',
                'protocol': 'tcp'
            },
        ]
    }
    with mock.patch.dict('foremast.securitygroup.create_securitygroup.DEFAULT_SECURITYGROUP_RULES', test_sg):
        sg = SpinnakerSecurityGroup()
        ingress = sg.update_default_rules()
        assert 'myapp' in ingress


@mock.patch('foremast.securitygroup.create_securitygroup.get_details')
@mock.patch('foremast.securitygroup.create_securitygroup.get_properties')
def test_securitygroup_references(mock_properties, mock_details):
    """Make sure default Security Groups are added to the ingress rules."""
    test_sg = {
        '$self': [
            {
                'start_port': '22',
                'end_port': '22',
                'protocol': 'tcp'
            },
        ]
    }

    sg = SpinnakerSecurityGroup(app='myapp')
    ingress = sg.resolve_self_references(test_sg)
    assert 'myapp' in ingress
    assert '22' == ingress['myapp'][0]['start_port']
    assert '22' == ingress['myapp'][0]['end_port']
