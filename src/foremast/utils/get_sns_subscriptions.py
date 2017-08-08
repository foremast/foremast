"""SNS Subscription functions."""
import logging

import boto3

from ..utils.awslambda import get_lambda_alias_arn

LOG = logging.getLogger(__name__)


def get_sns_subscriptions(app_name, env, region):
    """List SNS lambda subscriptions.

    Returns:
        list: List of Lambda subscribed SNS ARNs.

    """
    session = boto3.Session(profile_name=env, region_name=region)
    sns_client = session.client('sns')

    lambda_alias_arn = get_lambda_alias_arn(app=app_name, account=env, region=region)

    lambda_subscriptions = []
    subscriptions = sns_client.list_subscriptions()

    for subscription in subscriptions['Subscriptions']:
        if subscription['Protocol'] == "lambda" and subscription['Endpoint'] == lambda_alias_arn:
            lambda_subscriptions.append(subscription['SubscriptionArn'])

    if not lambda_subscriptions:
        LOG.debug('SNS subscription for function %s not found', lambda_alias_arn)

    return lambda_subscriptions
