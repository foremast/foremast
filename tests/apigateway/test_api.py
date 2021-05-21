"""Test API Gateway functions."""
from unittest import mock

from foremast.awslambda.api_gateway_event.api_gateway_event import APIGateway

TEST_RULES = {'api_name': 1, 'method': 'PUT'}


@mock.patch('foremast.awslambda.api_gateway_event.api_gateway_event.boto3')
@mock.patch('foremast.awslambda.api_gateway_event.api_gateway_event.get_details')
@mock.patch('foremast.awslambda.api_gateway_event.api_gateway_event.get_env_credential')
@mock.patch('foremast.awslambda.api_gateway_event.api_gateway_event.get_properties')
def test_apigateway(get_properties, get_env_credential, get_details, boto3):
    """Check basic object initialization."""
    test = APIGateway(rules=TEST_RULES)
    assert test


@mock.patch('foremast.awslambda.api_gateway_event.api_gateway_event.boto3')
@mock.patch('foremast.awslambda.api_gateway_event.api_gateway_event.get_details')
@mock.patch('foremast.awslambda.api_gateway_event.api_gateway_event.get_env_credential')
@mock.patch('foremast.awslambda.api_gateway_event.api_gateway_event.get_properties')
def test_create_resource(get_properties, get_env_credential, get_details, boto3):
    """Check creating API Resource."""
    test = APIGateway(rules=TEST_RULES)
    test.api_id = ''
    test.create_resource()

    test.client.create_resource.assert_called_with(restApiId='', parentId='', pathPart='')
