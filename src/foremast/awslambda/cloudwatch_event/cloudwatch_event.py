import logging
import boto3

from ...utils.lambda_event_exception import InvalidEventConfiguration
from ...utils.get_lambda_arn import get_lambda_arn

LOG = logging.getLogger(__name__)


def create_cloudwatch_event(app_name, env, region, rules):
    """
    Creates cloudwatch event for lambda from rules

    Returns:
        True if rule is created and attached to lambda
    """
    session = boto3.Session(profile_name=env, region_name=region)
    cloudwatch_client = session.client('events')

    rule_name = rules.get('rule_name')
    schedule = rules.get('schedule')
    rule_description = rules.get('rule_description')

    if schedule is None:
        LOG.critical('Schedule is required and no schedule is defined!')
        raise InvalidEventConfiguration('Schedule is required and no schedule is defined!')

    if rule_name is None:
        LOG.critical('Rule name is required and no rule_name is defined!')
        raise InvalidEventConfiguration('Rule name is required and no rule_name is defined!')
    else:
        # TODO: check if this is the right logic
        LOG.info('%s and %s', app_name, rule_name)
        # TODO: maybe we need to sanitize more?
        rule_name = "{}_{}".format(app_name, rule_name.replace(' ', '_'))

    if rule_description is None:
        rule_description = "{} - {}".format(app_name, rule_name)

    # Create Cloudwatch rule
    # Create Cloudwatch rule
    cloudwatch_client.put_rule(Name=rule_name,
                               ScheduleExpression=schedule,
                               State='ENABLED',
                               Description=rule_description)

    lambda_arn = get_lambda_arn(app=app_name, account=env, region=region)

    targets = []
    # TODO: read this one from file event-config-*.json
    json_payload = {}

    target = {
        "Id": app_name,
        "Arn": lambda_arn,
        "Input": json_payload
    }

    targets.append(target)

    cloudwatch_client.put_targets(Rule=rule_name, Targets=targets)

    return True

