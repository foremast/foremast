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

"""Lambda related utilities"""
import logging

import boto3

from ..exceptions import LambdaAliasDoesNotExist, LambdaFunctionDoesNotExist

LOG = logging.getLogger(__name__)


def get_lambda_arn(app, account, region):
    """Get lambda ARN.

    Args:
        account (str): AWS account name.
        region (str): Region name, e.g. us-east-1
        app (str): Lambda function name

    Returns:
        str: ARN for requested lambda function
    """
    session = boto3.Session(profile_name=account, region_name=region)
    lambda_client = session.client('lambda')

    lambda_functions = lambda_client.list_functions()['Functions']

    for lambda_function in lambda_functions:
        if lambda_function['FunctionName'] == app:
            lambda_arn = lambda_function['FunctionArn']
            LOG.debug("Lambda ARN for lambda function %s is %s.", app, lambda_arn)
            return lambda_arn
    else:
        LOG.fatal('Lambda function with name %s not found in %s %s', app, account, region)
        raise LambdaFunctionDoesNotExist('Lambda function with name {0} not found in {1} {2}'.format(app, account,
                                                                                                     region))


def get_lambda_alias_arn(app, account, region):
    """Get lambda alias ARN. Assumes that account name is equal to alias name.

    Args:
        account (str): AWS account name.
        region (str): Region name, e.g. us-east-1
        app (str): Lambda function name

    Returns:
        str: ARN for requested lambda alias
    """
    session = boto3.Session(profile_name=account, region_name=region)
    lambda_client = session.client('lambda')

    lambda_aliases = lambda_client.list_aliases(FunctionName=app)

    for alias in lambda_aliases['Aliases']:
        if alias['Name'] == account:
            lambda_alias_arn = alias['AliasArn']
            LOG.info('Found ARN for alias %s for function %s', account, app)
            return lambda_alias_arn
    else:
        LOG.fatal('Lambda alias %s of function %s not found', account, app)
        raise LambdaAliasDoesNotExist('Lambda alias %s of function %s not found'.format(account, app))


def add_lambda_permissions(function='',
                           statement_id='',
                           action='lambda:InvokeFunction',
                           principal='',
                           source_arn='',
                           env='',
                           region='us-east-1'):
    """Add permission to Lambda for the event trigger.

    Args:
        function (str): Lambda function name
        statement_id (str): IAM policy statement (principal) id
        action (str): Lambda action to allow
        principal (str): AWS principal to add permissions
        source_arn (str): ARN of the source of the event. Only needed for S3
        env (str): Environment/account of function
        region (str): AWS region of function
    """
    session = boto3.Session(profile_name=env, region_name=region)
    lambda_client = session.client('lambda')
    response_action = None

    add_permissions_kwargs = {
        'FunctionName': function,
        'StatementId': statement_id,
        'Action': action,
        'Principal': principal,
    }
    if source_arn:
        add_permissions_kwargs['SourceArn'] = source_arn

    try:
        lambda_client.add_permission(**add_permissions_kwargs)
        response_action = 'Add permission with Sid: {}'.format(statement_id)
    except boto3.exceptions.botocore.exceptions.ClientError:
        response_action = "Did not add permissions"

    LOG.debug('Related StatementId (SID): %s', statement_id)
    LOG.info(response_action)
