"""SNS Subscription functions."""
import logging

import boto3

from ..utils.awslambda import get_lambda_alias_arn

LOG = logging.getLogger(__name__)


def get_dynamodb_streams_triggers(app_name, env, region):
    """List DynamoDB Streams lambda triggers.

    Returns:
        list: List of Lambda triggers DynamoDB Streams ARNs.

    """
    session = boto3.Session(profile_name=env, region_name=region)
    sns_client = session.client('dynamodb')

    lambda_alias_arn = get_lambda_alias_arn(app=app_name, account=env, region=region)

    lambda_triggers = []
    triggers = sns_client.list_subscriptions()

    for subscription in triggers['Subscriptions']:
        if subscription['Protocol'] == "lambda" and subscription['Endpoint'] == lambda_alias_arn:
            triggers.append(subscription['SubscriptionArn'])

    if not lambda_triggers:
        LOG.debug('DynamoDB Streams triggers for function %s not found', lambda_alias_arn)

    return lambda_triggers
