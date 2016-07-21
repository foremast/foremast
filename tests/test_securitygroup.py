"""Ensure Security Groups get created properly"""
import json
from unittest.mock import patch
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


@patch('foremast.securitygroup.create_securitygroup.check_task')
@patch('requests.post')
@patch("foremast.securitygroup.create_securitygroup.get_properties")
def test_create_crossaccount_securitygroup(pipeline_config,
                                           requests, check_task_mock):
    """Should create SG with cross account true"""
    check_task_mock.return_value = True
    requests.return_value.ok.return_value = True
    pipeline_config.return_value = json.loads(SAMPLE_JSON)

    x = SpinnakerSecurityGroup(app='edgeforrest',
                               env='dev',
                               region='us-east-1')
    assert x.create_security_group() is True
