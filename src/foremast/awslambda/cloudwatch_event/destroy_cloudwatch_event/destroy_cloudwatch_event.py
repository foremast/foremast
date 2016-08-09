"""Destroy any DNS records."""
import logging

import boto3

from ....utils.get_cloudwatch_event_rule_name import get_event_rule_by_target

LOG = logging.getLogger(__name__)


def destroy_cloudwatch_event(app='', env='dev', region=''):
    """Destroy Cloudwatch event subscription.

    Args:
        app (str): Spinnaker Application name.
        env (str): Deployment environment.
        region (str): AWS region.
    Returns:
        bool: True upon successful completion.
    """

    session = boto3.Session(profile_name=env, region_name=region)
    cloudwatch_client = session.client('events')

    event_rules = get_event_rule_by_target(app_name=app, account=env, region=region)

    for rule in event_rules:
        cloudwatch_client.remove_targets(
            Rule=rule,
            Ids=[app]
        )

    return True
