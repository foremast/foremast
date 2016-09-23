#   Foremast - Pipeline Tooling
#
#   Copyright 2016 Gogo, LLC
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

import json
import logging

import boto3

from ...exceptions import InvalidEventConfiguration
from ...utils import add_lambda_permissions, get_env_credential, get_lambda_alias_arn

LOG = logging.getLogger(__name__)


def create_cloudwatch_event(app_name, env, region, rules):
    """Create cloudwatch event for lambda from rules.

    Args:
        app_name (str): name of the lambda function
        env (str): Environment/Account for lambda function
        region (str): AWS region of the lambda function
        rules (str): Trigger rules from the settings
    """

    session = boto3.Session(profile_name=env, region_name=region)
    cloudwatch_client = session.client('events')

    rule_name = rules.get('rule_name')
    schedule = rules.get('schedule')
    rule_description = rules.get('rule_description')
    json_input = rules.get('json_input', {})

    if schedule is None:
        LOG.critical('Schedule is required and no schedule is defined!')
        raise InvalidEventConfiguration('Schedule is required and no schedule is defined!')

    if rule_name is None:
        LOG.critical('Rule name is required and no rule_name is defined!')
        raise InvalidEventConfiguration('Rule name is required and no rule_name is defined!')
    else:
        LOG.info('%s and %s', app_name, rule_name)
        rule_name = "{}_{}".format(app_name, rule_name.replace(' ', '_'))

    if rule_description is None:
        rule_description = "{} - {}".format(app_name, rule_name)

    lambda_alias_arn = get_lambda_alias_arn(app=app_name, account=env, region=region)

    #Add lambda permissions
    account_id = get_env_credential(env=env)['accountId']
    principal = "events.amazonaws.com"
    statement_id = '{}_cloudwatch_{}'.format(app_name, rule_name)
    source_arn = 'arn:aws:events:{}:{}:rule/{}'.format(region, account_id, rule_name)
    add_lambda_permissions(function=lambda_alias_arn,
                           statement_id=statement_id,
                           action='lambda:InvokeFunction',
                           principal=principal,
                           source_arn=source_arn,
                           env=env,
                           region=region)

    # Create Cloudwatch rule
    cloudwatch_client.put_rule(Name=rule_name,
                               ScheduleExpression=schedule,
                               State='ENABLED',
                               Description=rule_description)

    targets = []
    # TODO: read this one from file event-config-*.json
    json_payload = '{}'.format(json.dumps(json_input))

    target = {"Id": app_name, "Arn": lambda_alias_arn, "Input": json_payload}

    targets.append(target)

    cloudwatch_client.put_targets(Rule=rule_name, Targets=targets)

    LOG.info("Created Cloudwatch event with schedule: %s", schedule)
