"""Test API Gateway functions."""
from unittest import mock

from foremast.awslambda.api_gateway_event.api_gateway_event import APIGateway


@mock.patch('foremast.awslambda.api_gateway_event.api_gateway_event.boto3')
@mock.patch('foremast.awslambda.api_gateway_event.api_gateway_event.get_details')
@mock.patch('foremast.awslambda.api_gateway_event.api_gateway_event.get_env_credential')
@mock.patch('foremast.awslambda.api_gateway_event.api_gateway_event.get_properties')
def test_create_resource(get_properties, get_env_credential, get_details, boto3):
    """Check creating API Resource."""
    test_rules = {'api_name': 1, 'method': 'PUT'}

    test = APIGateway(rules=test_rules)
    test.api_id = ''
    test.create_resource()

    test.client.create_resource.assert_called_with(restApiId='', parentId='', pathPart='/')
