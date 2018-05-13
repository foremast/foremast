#   Foremast - Pipeline Tooling
#
#   Copyright 2018 Gogo, LLC
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
"""Lambda related utilities."""
import json
import logging

import boto3

from ..exceptions import LambdaAliasDoesNotExist, LambdaFunctionDoesNotExist

LOG = logging.getLogger(__name__)
FOREMAST_PREFIX = "foremast-"


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

    lambda_arn = None
    paginator = lambda_client.get_paginator('list_functions')

    for lambda_functions in paginator.paginate():
        for lambda_function in lambda_functions['Functions']:
            if lambda_function['FunctionName'] == app:
                lambda_arn = lambda_function['FunctionArn']
                LOG.debug("Lambda ARN for lambda function %s is %s.", app, lambda_arn)
                break
        if lambda_arn:
            break

    if not lambda_arn:
        LOG.fatal('Lambda function with name %s not found in %s %s', app, account, region)
        raise LambdaFunctionDoesNotExist(
            'Lambda function with name {0} not found in {1} {2}'.format(app, account, region))

    return lambda_arn


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

    matched_alias = None
    for alias in lambda_aliases['Aliases']:
        if alias['Name'] == account:
            lambda_alias_arn = alias['AliasArn']
            LOG.info('Found ARN for alias %s for function %s', account, app)
            matched_alias = lambda_alias_arn
            break
    else:
        fatal_message = 'Lambda alias {0} of function {1} not found'.format(account, app)
        LOG.fatal(fatal_message)
        raise LambdaAliasDoesNotExist(fatal_message)
    return matched_alias


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
        source_arn (str): ARN of the source of the event.
        env (str): Environment/account of function
        region (str): AWS region of function
    """
    session = boto3.Session(profile_name=env, region_name=region)
    lambda_client = session.client('lambda')
    response_action = None
    prefixed_sid = FOREMAST_PREFIX + statement_id

    add_permissions_kwargs = {
        'FunctionName': function,
        'StatementId': prefixed_sid,
        'Action': action,
        'Principal': principal,
    }

    if source_arn:
        add_permissions_kwargs['SourceArn'] = source_arn

    try:
        lambda_client.add_permission(**add_permissions_kwargs)
        response_action = 'Add permission with Sid: {}'.format(prefixed_sid)
    except boto3.exceptions.botocore.exceptions.ClientError as error:
        LOG.debug('Add permission error: %s', error)
        response_action = "Did not add permissions"

    LOG.debug('Related StatementId (SID): %s', prefixed_sid)
    LOG.info(response_action)


def remove_all_lambda_permissions(app_name='', env='', region='us-east-1'):
    """Remove all foremast-* permissions from lambda.

    Args:
        app_name (str): Application name
        env (str): AWS environment
        region (str): AWS region
    """
    session = boto3.Session(profile_name=env, region_name=region)
    lambda_client = session.client('lambda')
    legacy_prefix = app_name + "_"

    lambda_arn = get_lambda_arn(app_name, env, region)
    lambda_alias_arn = get_lambda_alias_arn(app_name, env, region)
    arns = (lambda_arn, lambda_alias_arn)

    for arn in arns:
        try:
            response = lambda_client.get_policy(FunctionName=arn)
        except boto3.exceptions.botocore.exceptions.ClientError as error:
            LOG.info("No policy exists for function %s, skipping deletion", arn)
            LOG.debug(error)
            continue

        policy_json = json.loads(response['Policy'])
        LOG.debug("Found Policy: %s", response)
        for perm in policy_json['Statement']:
            if perm['Sid'].startswith(FOREMAST_PREFIX) or perm['Sid'].startswith(legacy_prefix):
                lambda_client.remove_permission(FunctionName=arn, StatementId=perm['Sid'])
                LOG.info('removed permission: %s', perm['Sid'])
            else:
                LOG.info('Skipping deleting permission %s - Not managed by Foremast', perm['Sid'])
