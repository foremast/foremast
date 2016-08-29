"""Test AWS Lambda Utilities."""
from unittest import mock

import boto3
from foremast.utils.awslambda import add_lambda_permissions

ERROR_RESPONSE = {'Error': {}}


@mock.patch('foremast.utils.awslambda.boto3')
@mock.patch('foremast.utils.awslambda.LOG')
def test_add_lambda_permission_success(LOG, mock_boto3):
    """Check lambda permssion add successful."""
    add_lambda_permissions()

    args, _ = LOG.info.call_args
    assert args[0].startswith('Add permission')


@mock.patch('foremast.utils.awslambda.boto3.Session')
@mock.patch('foremast.utils.awslambda.LOG')
def test_add_lambda_permission_failure(LOG, session):
    """Check lambda permssion add failure."""
    client = session.return_value.client.return_value
    client.add_permission.side_effect = boto3.exceptions.botocore.exceptions.ClientError(ERROR_RESPONSE,
                                                                                         'operation_name')

    add_lambda_permissions()

    args, _ = LOG.info.call_args
    assert args[0].startswith('Did not add')
