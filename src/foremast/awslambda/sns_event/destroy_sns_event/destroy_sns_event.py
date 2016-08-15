import logging
import boto3

from ....utils.get_sns_subscriptions import get_sns_subscriptions

LOG = logging.getLogger(__name__)


def destroy_sns_event(app_name, env, region):
    """ Destroys all Lambda SNS subscription

    Returns:
        boolean: True if subscription destroyed successfully
    """
    session = boto3.Session(profile_name=env, region_name=region)
    sns_client = session.client('sns')

    lambda_subscriptions = get_sns_subscriptions(app_name=app_name, env=env, region=region)

    for subscription_arn in lambda_subscriptions:
        sns_client.unsubscribe(
            SubscriptionArn=subscription_arn
        )

    LOG.debug("Lambda SNS event deleted")
    return True
