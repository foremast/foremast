import logging

import boto3

from ...exceptions import InvalidEventConfiguration
from ...utils import add_lambda_permissions, get_env_credential, get_lambda_arn

LOG = logging.getLogger(__name__)


def create_cloudwatch_log_event(app_name, env, region, rules):
    """Creates cloudwatch log event for lambda from rules

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

    if not filter_pattern:
        LOG.critical('Filter pattern is required and no filter_pattern is defined!')
        raise InvalidEventConfiguration('Filter pattern is required and no filter_pattern is defined!')

    lambda_arn = get_lambda_arn(app=app_name, account=env, region=region)

    statement_id = '{}_cloudwatchlog_{}'.format(app_name, filter_name.replace(" ", "_"))
    principal = 'logs.{}.amazonaws.com'.format(region)
    account_id = get_env_credential(env=env)['accountId']
    source_arn = "arn:aws:logs:{0}:{1}:log-group:{2}:*".format(region, account_id, log_group)
    add_lambda_permissions(function=app_name,
                           statement_id=statement_id,
                           action='lambda:InvokeFunction',
                           principal=principal,
                           source_arn=source_arn,
                           env=env,
                           region=region)

    cloudwatch_client.put_subscription_filter(
        logGroupName=log_group,
        filterName=filter_name,
        filterPattern=filter_pattern,
        destinationArn=lambda_arn
    )

    LOG.info("Created Cloudwatch log event with filter: %s", filter_pattern)
