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
"""Create cloudwatch events"""

import json
import logging

import boto3

from ...exceptions import InvalidEventConfiguration
from ...utils import add_lambda_permissions, get_env_credential, get_lambda_arn

LOG = logging.getLogger(__name__)


def create_cloudwatch_event(app_name, env, region, rules):
    """Create cloudwatch event for lambda from rules.

    Args:
        app_name (str): name of the lambda function
        env (str): Environment/Account for lambda function
        region (str): AWS region of the lambda function
        rules (dict): Trigger rules from the settings
    """
    session = boto3.Session(profile_name=env, region_name=region)
    cloudwatch_client = session.client('events')

    rule_name = rules.get('rule_name')
    rule_type = rules.get('rule_type', 'schedule')
    schedule = rules.get('schedule')
    event_pattern = rules.get('event_pattern')
    rule_description = rules.get('rule_description')
    json_input = rules.get('json_input', {})

    if rule_type == 'schedule' and schedule is None:
        LOG.critical('A CloudWatch Schedule is required and no schedule pattern is defined!')
        raise InvalidEventConfiguration('A CloudWatch Schedule is required and no schedule is defined!')

    if rule_type == 'event_pattern' and event_pattern is None:
        LOG.critical('A CloudWatch Event Pattern is required and no event pattern is defined!')
        raise InvalidEventConfiguration('A CloudWatch Event Pattern is required and no event pattern is defined!')

    if rule_name is None:
        LOG.critical('Rule name is required and no rule_name is defined!')
        raise InvalidEventConfiguration('Rule name is required and no rule_name is defined!')
    else:
        LOG.info('%s and %s', app_name, rule_name)
        rule_name = "{}_{}".format(app_name, rule_name.replace(' ', '_'))

    if rule_description is None:
        rule_description = "{} - {}".format(app_name, rule_name)

    lambda_arn = get_lambda_arn(app=app_name, account=env, region=region)

    # Add lambda permissions
    account_id = get_env_credential(env=env)['accountId']
    principal = "events.amazonaws.com"
    statement_id = 'cloudwatch_{}'.format(rule_name)
    source_arn = 'arn:aws:events:{}:{}:rule/{}'.format(region, account_id, rule_name)
    add_lambda_permissions(
        function=lambda_arn,
        statement_id=statement_id,
        action='lambda:InvokeFunction',
        principal=principal,
        source_arn=source_arn,
        env=env,
        region=region)

    # Create CloudWatch rule
    if rule_type == 'schedule':
        cloudwatch_client.put_rule(
            Name=rule_name,
            ScheduleExpression=schedule,
            State='ENABLED',
            Description=rule_description)
        LOG.info('Created CloudWatch Rule "%s" with %s: %s', rule_name, rule_type, schedule)
    elif rule_type == 'event_pattern':
        cloudwatch_client.put_rule(
            Name=rule_name,
            EventPattern=json.dumps(event_pattern),
            State='ENABLED',
            Description=rule_description)
        LOG.info('Created CloudWatch Rule "%s" with %s: %s', rule_name, rule_type, event_pattern)

    targets = [{
        "Id": app_name,
        "Arn": lambda_arn,
    }]

    if json_input:
        json_payload = '{}'.format(json.dumps(json_input))
        for each_target in targets:
            each_target['Input'] = json_payload

    put_targets_response = cloudwatch_client.put_targets(Rule=rule_name, Targets=targets)
    LOG.debug('CloudWatch PutTargets Response: %s', put_targets_response)
    LOG.info('Configured CloudWatch Rule Target: %s', lambda_arn)
