"""Verify AWS Lambda Function creation."""
import copy
from unittest import mock

from foremast.awslambda.awslambda import LambdaFunction

TEST_PROPERTIES = {
    'pipeline': {
        'lambda': {
            'app_description': None,
            'handler': None,
            'runtime': None,
            'vpc_enabled': None,
        },
    },
    'app': {
        'custom_tags': {},
        'lambda_memory': 0,
        'lambda_timeout': 0,        
        'lambda_environment': None,
        'lambda_layers': None,
        'lambda_dlq': None,
        'lambda_tracing': None,
        'lambda_destinations': None,
        'lambda_subnet_count': None,
        'lambda_subnet_purpose': 'internal',
        'lambda_filesystems': None,
        'lambda_provisioned_throughput': None,
    }
}
GENERATED_IAM = {
    'lambda_role': 'generated_role',
}


@mock.patch('foremast.awslambda.awslambda.boto3')
@mock.patch('foremast.awslambda.awslambda.get_details')
@mock.patch('foremast.awslambda.awslambda.get_properties')
@mock.patch('foremast.awslambda.awslambda.get_role_arn')
def test_role_arn(mock_get_role_arn, mock_get_properties, mock_get_details, mock_boto3):
    """Check Role ARN configuration."""
    generated = copy.deepcopy(GENERATED_IAM)
    properties = copy.deepcopy(TEST_PROPERTIES)

    mock_get_details.return_value.iam.return_value = generated
    mock_get_properties.return_value = properties

    LambdaFunction(app='test_app', env='test_env', region='us-east-1', prop_path='other')
    mock_get_role_arn.assert_called_with(generated['lambda_role'], mock.ANY, mock.ANY)


@mock.patch('foremast.awslambda.awslambda.boto3')
@mock.patch('foremast.awslambda.awslambda.get_details')
@mock.patch('foremast.awslambda.awslambda.get_properties')
@mock.patch('foremast.awslambda.awslambda.get_role_arn')
def test_role_arn_none(mock_get_role_arn, mock_get_properties, mock_get_details, mock_boto3):
    """Generated Role should be used for Lambda."""
    generated = copy.deepcopy(GENERATED_IAM)
    properties = copy.deepcopy(TEST_PROPERTIES)
    properties['app']['lambda_role'] = None

    mock_get_details.return_value.iam.return_value = generated
    mock_get_properties.return_value = properties

    LambdaFunction(app='test_app', env='test_env', region='us-east-1', prop_path='other')
    mock_get_role_arn.assert_called_with(GENERATED_IAM['lambda_role'], mock.ANY, mock.ANY)


@mock.patch('foremast.awslambda.awslambda.boto3')
@mock.patch('foremast.awslambda.awslambda.get_details')
@mock.patch('foremast.awslambda.awslambda.get_properties')
@mock.patch('foremast.awslambda.awslambda.get_role_arn')
def test_role_arn_custom(mock_get_role_arn, mock_get_properties, mock_get_details, mock_boto3):
    """Custom Role should be used for Lambda."""
    custom_role = 'custom_role'
    generated = copy.deepcopy(GENERATED_IAM)
    properties = copy.deepcopy(TEST_PROPERTIES)
    properties['app']['lambda_role'] = custom_role

    mock_get_details.return_value.iam.return_value = generated
    mock_get_properties.return_value = properties

    LambdaFunction(app='test_app', env='test_env', region='us-east-1', prop_path='other')
    mock_get_role_arn.assert_called_with(custom_role, mock.ANY, mock.ANY)
