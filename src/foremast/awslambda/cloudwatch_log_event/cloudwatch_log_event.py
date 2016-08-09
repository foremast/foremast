import logging
import boto3

from ...utils.lambda_event_exception import InvalidEventConfiguration
from ...utils.get_lambda_arn import get_lambda_arn

LOG = logging.getLogger(__name__)


def create_cloudwatch_log_event(app_name, env, region, rules):
    """
    Creates cloudwatch log event for lambda from rules

    Returns:
        str: True if rule is created successfully
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

    cloudwatch_client.put_subscription_filter(
        logGroupName=log_group,
        filterName=filter_name,
        filterPattern=filter_pattern,
        destinationArn=lambda_arn
    )

    return True

