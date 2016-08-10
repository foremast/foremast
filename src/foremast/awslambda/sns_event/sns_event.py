import logging
import boto3

from ...utils.get_sns_topic_arn import get_sns_topic_arn
from ...utils.get_lambda_arn import get_lambda_arn

LOG = logging.getLogger(__name__)


def create_sns_event(app_name, env, region, rules):
    """ Creates SNS lambda event from rules

    Returns:
        boolean: True if event created successfully
    """
    session = boto3.Session(profile_name=env, region_name=region)
    sns_client = session.client('sns')

    topic_name = rules.get('topic')
    lambda_arn = get_lambda_arn(app=app_name, account=env, region=region)
    topic_arn = get_sns_topic_arn(topic_name=topic_name, account=env, region=region)
    protocol = 'lambda'

    sns_client.subscribe(TopicArn=topic_arn, Protocol=protocol, Endpoint=lambda_arn)
    LOG.debug("SNS Lambda event created")

    return True
