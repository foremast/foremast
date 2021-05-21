"""Test AWS Lambda Utilities."""
from unittest import mock

import boto3
import pytest

from foremast.exceptions import LambdaAliasDoesNotExist
from foremast.utils.awslambda import add_lambda_permissions, get_lambda_alias_arn

ERROR_RESPONSE = {'Error': {}}


def lambda_alias_list_mock():
    return_dict = {
        'Aliases': [{
            'Description': '',
            'AliasArn': 'arn:aws:lambda:us-east-1:222572804561:function:lambdatest2:stage',
            'FunctionVersion': '$LATEST',
            'Name': 'stage'
        }, {
            'Description': '',
            'AliasArn': 'arn:aws:lambda:us-east-1:222572804561:function:lambdatest2:dev',
            'FunctionVersion': '$LATEST',
            'Name': 'dev'
        }]
    }
    return return_dict


def lambda_no_alias_list_mock():
    return_dict = {'Aliases': []}
    return return_dict


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
    client.add_permission.side_effect = boto3.exceptions.botocore.exceptions.ClientError(
        ERROR_RESPONSE, 'operation_name')

    add_lambda_permissions()

    args, _ = LOG.info.call_args
    assert args[0].startswith('Did not add')


@mock.patch('foremast.utils.awslambda.boto3.Session')
@mock.patch('foremast.utils.awslambda.LOG')
def test_get_lambda_alias_arn_success(LOG, mock_boto3):
    """Check get lambda alias arn."""
    client = mock_boto3.return_value.client.return_value
    client.list_aliases.return_value = lambda_alias_list_mock()

    rv = get_lambda_alias_arn('lambdatest', 'dev', 'us-east-1')

    args, _ = LOG.info.call_args

    assert rv == 'arn:aws:lambda:us-east-1:222572804561:function:lambdatest2:dev'
    assert args[0].startswith('Found ARN for alias')


@mock.patch('foremast.utils.awslambda.boto3.Session')
def test_get_lambda_alias_arn_failure(mock_boto3):
    """Check get lambda alias arn failure."""
    client = mock_boto3.return_value.client.return_value
    client.list_aliases.return_value = lambda_no_alias_list_mock()

    with pytest.raises(LambdaAliasDoesNotExist):
        get_lambda_alias_arn('lambdatest', 'dev', 'us-east-1')
