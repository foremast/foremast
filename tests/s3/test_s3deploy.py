"""Test S3 Deploy"""

import pytest
from unittest import mock

from foremast import s3

@pytest.fixture
@mock.patch('foremast.s3.s3deploy.get_properties')
@mock.patch('foremast.s3.s3deploy.get_details')
def s3deployment(mock_get_details, mock_get_props):
    """Creates S3Deployment Fixture"""
    mock_get_props.return_value = {"deploy_strategy": "highlander",
                                   "s3": {"path": "/"}}
    mock_get_details.return_value.s3_app_bucket.return_value = "testapp"
    deployobj = s3.S3Deployment(app="testapp",
                                env="dev",
                                region="us-east-1",
                                prop_path="/",
                                artifact_path="/artifact",
                                artifact_branch="master",
                                artifact_version="1")
    return deployobj

def test_get_cmd(s3deployment):
    """Tests s3.S3Deployment._get_upload_cmd returns correct cmd"""
    expected_nomirror_cmd = "aws s3 sync /artifact s3://testapp/1 --delete --exact-timestamps --profile dev"
    expected_mirror_cmd = "aws s3 sync /artifact s3://testapp/ --delete --exact-timestamps --profile dev"
    actual_nomirror_cmd = s3deployment._get_upload_cmd(deploy_strategy="highlander")
    actual_mirror_cmd = s3deployment._get_upload_cmd(deploy_strategy="mirror")
    assert actual_nomirror_cmd == expected_nomirror_cmd
    assert actual_mirror_cmd == expected_mirror_cmd

def test_path_formatter(s3deployment):
    """Tests s3.S3Deployment._path_formatter returns correct path"""
    expected_latest_path = "s3://testapp/LATEST"
    expected_mirror_path = "s3://testapp/"
    actual_latest_path = s3deployment._path_formatter("LATEST")
    actual_mirror_path = s3deployment._path_formatter("MIRROR")
    assert actual_latest_path == expected_latest_path
    assert actual_mirror_path == expected_mirror_path
