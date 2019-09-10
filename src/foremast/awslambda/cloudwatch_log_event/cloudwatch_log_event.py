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
"""Create cloudwatch log event"""

import logging

import boto3

from ...exceptions import InvalidEventConfiguration
from ...utils import add_lambda_permissions, get_env_credential, get_lambda_alias_arn

LOG = logging.getLogger(__name__)


def create_cloudwatch_log_event(app_name, env, region, rules):
    """Create cloudwatch log event for lambda from rules.

    Args:
        app_name (str): name of the lambda function
        env (str): Environment/Account for lambda function
        region (str): AWS region of the lambda function
        rules (str): Trigger rules from the settings
    """

    session = boto3.Session(profile_name=env, region_name=region)
    cloudwatch_client = session.client('logs')

    log_group = rules.get('log_group')
    filter_name = rules.get('filter_name')
    filter_pattern = rules.get('filter_pattern')

    if not log_group:
        LOG.critical('Log group is required and no "log_group" is defined!')
        raise InvalidEventConfiguration('Log group is required and no "log_group" is defined!')

    if not filter_name:
        LOG.critical('Filter name is required and no filter_name is defined!')
        raise InvalidEventConfiguration('Filter name is required and no filter_name is defined!')

    if filter_pattern is None:
        LOG.critical('Filter pattern is required and no filter_pattern is defined!')
        raise InvalidEventConfiguration('Filter pattern is required and no filter_pattern is defined!')

    lambda_alias_arn = get_lambda_alias_arn(app=app_name, account=env, region=region)

    statement_id = '{}_cloudwatchlog_{}'.format(app_name, filter_name.replace(" ", "_"))
    principal = 'logs.{}.amazonaws.com'.format(region)
    account_id = get_env_credential(env=env)['accountId']
    source_arn = "arn:aws:logs:{0}:{1}:log-group:{2}:*".format(region, account_id, log_group)
    add_lambda_permissions(
        function=lambda_alias_arn,
        statement_id=statement_id,
        action='lambda:InvokeFunction',
        principal=principal,
        source_arn=source_arn,
        env=env,
        region=region)

    cloudwatch_client.put_subscription_filter(
        logGroupName=log_group, filterName=filter_name, filterPattern=filter_pattern, destinationArn=lambda_alias_arn)

    LOG.info("Created Cloudwatch log event with filter: %s", filter_pattern)
