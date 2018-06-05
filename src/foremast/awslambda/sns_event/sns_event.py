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
"""Create SNS event for lambda"""

import logging

import boto3

from ...utils import add_lambda_permissions, get_lambda_alias_arn, get_sns_topic_arn

LOG = logging.getLogger(__name__)


def create_sns_event(app_name, env, region, rules):
    """Create SNS lambda event from rules.

    Args:
        app_name (str): name of the lambda function
        env (str): Environment/Account for lambda function
        region (str): AWS region of the lambda function
        rules (str): Trigger rules from the settings
    """
    session = boto3.Session(profile_name=env, region_name=region)
    sns_client = session.client('sns')

    topic_name = rules.get('topic')
    lambda_alias_arn = get_lambda_alias_arn(app=app_name, account=env, region=region)
    topic_arn = get_sns_topic_arn(topic_name=topic_name, account=env, region=region)
    protocol = 'lambda'

    statement_id = '{}_sns_{}'.format(app_name, topic_name)
    principal = 'sns.amazonaws.com'
    add_lambda_permissions(
        function=lambda_alias_arn,
        statement_id=statement_id,
        action='lambda:InvokeFunction',
        principal=principal,
        source_arn=topic_arn,
        env=env,
        region=region)

    sns_client.subscribe(TopicArn=topic_arn, Protocol=protocol, Endpoint=lambda_alias_arn)
    LOG.debug("SNS Lambda event created")

    LOG.info("Created SNS event subscription on topic %s", topic_name)
