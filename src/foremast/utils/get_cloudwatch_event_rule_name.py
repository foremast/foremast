import logging

import boto3

from ..utils.get_lambda_arn import get_lambda_arn

LOG = logging.getLogger(__name__)


def get_event_rule_by_target(app_name, account, region):
    session = boto3.Session(profile_name=account, region_name=region)
    cloudwatch_client = session.client('events')

    lambda_arn = get_lambda_arn(app=app_name, account=account, region=region)
    rule_names = cloudwatch_client.list_rule_names_by_target(TargetArn=lambda_arn)

    if rule_names['RuleNames']:
        return rule_names['RuleNames']
    else:
        LOG.debug("No event rules found")



