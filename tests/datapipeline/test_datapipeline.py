"""Verify AWS Data Pipeline Creation."""
from unittest import mock

import copy
import awscli.customizations.datapipeline.translator
from foremast.datapipeline.datapipeline import AWSDataPipeline

GOOD_DEF = 	{
        "objects": [],
        "parameters": [],
        "values": {}
        }

BAD_DEF = 	{
        "no_object": [],
        "parameters": [],
        "values": {}
        }

TEST_PROPERTIES = {
    'test_env': {
        'datapipeline': {
            'name': 'Test Pipeline',
            'description': "this is a test",
            'json_definition': GOOD_DEF
        }
    }
}

@mock.patch('foremast.datapipeline.datapipeline.boto3.Session.client')
@mock.patch('foremast.datapipeline.datapipeline.get_details')
@mock.patch('foremast.datapipeline.datapipeline.get_properties')
def test_create_datapipeline(mock_get_properties, mock_get_details, mock_boto3):
    """Check data pipeline creation"""
    generated = {"project": "test"}
    properties = copy.deepcopy(TEST_PROPERTIES)
    mock_get_details.return_value.data = generated
    mock_get_properties.return_value = properties
    mock_boto3.return_value.create_pipeline.return_value = {}

    dp = AWSDataPipeline(app='test_app', env='test_env', region='us-east-1', prop_path='other')
    dp.create_datapipeline()
    assert dp.pipeline_id == None

@mock.patch('foremast.datapipeline.datapipeline.boto3.Session.client')
@mock.patch('foremast.datapipeline.datapipeline.get_details')
@mock.patch('foremast.datapipeline.datapipeline.get_properties')
def test_set_pipeline_definition(mock_get_properties, mock_get_details, mock_boto3):
    """Tests that pipeline definition is set correctly"""
    generated = {"project": "test"}
    properties = copy.deepcopy(TEST_PROPERTIES)
    mock_get_details.return_value.data = generated
    mock_get_properties.return_value = properties

    good_dp = AWSDataPipeline(app='test_app', env='test_env', region='us-east-1', prop_path='other')
    good_dp.pipeline_id='1'
    try:
        good_dp.set_pipeline_definition()
        assert True
    except awscli.customizations.datapipeline.translator.PipelineDefinitionError:
        assert False

    properties['test_env']['datapipeline']['json_definition'] = BAD_DEF
    mock_get_properties.return_value = properties
    bad_dp = AWSDataPipeline(app='test_app', env='test_env', region='us-east-1', prop_path='other')
    bad_dp.pipeline_id='1'
    try:
        bad_dp.set_pipeline_definition()
        assert False
    except awscli.customizations.datapipeline.translator.PipelineDefinitionError:
        assert True

@mock.patch('foremast.datapipeline.datapipeline.boto3.Session.client')
@mock.patch('foremast.datapipeline.datapipeline.get_details')
@mock.patch('foremast.datapipeline.datapipeline.get_properties')
def test_get_pipeline_id(mock_get_properties, mock_get_details, mock_boto3):
    """Tests getting the pipeline ID from boto3"""
    test_pipelines = {'pipelineIdList': [
        {
            "name": "Test Pipeline",
            "id": "1234"
        },
        {
            "name": "Other",
            "id": "5678"
        }
    ] }
    generated = {"project": "test"}
    properties = copy.deepcopy(TEST_PROPERTIES)
    mock_get_details.return_value.data = generated
    mock_get_properties.return_value = properties
    mock_boto3.return_value.list_pipelines.return_value = test_pipelines

    dp = AWSDataPipeline(app='test_app', env='test_env', region='us-east-1', prop_path='other')
    dp.get_pipeline_id()
    assert dp.pipeline_id == '1234'
