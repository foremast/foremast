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
"""Create DynamoDB Streams event for lambda"""

import logging

import boto3

from ...utils import add_lambda_permissions, get_lambda_alias_arn, get_dynamodb_streams_arn

LOG = logging.getLogger(__name__)


def create_dynamodb_streams_event(app_name, env, region, rules):
    """Create DynamoDB Streams lambda event from rules.

    Args:
        app_name (str): name of the lambda function
        env (str): Environment/Account for lambda function
        region (str): AWS region of the lambda function
        rules (str): Trigger rules from the settings
    """
    session = boto3.Session(profile_name=env, region_name=region)
    lambda_client = session.client('lambda')

    trigger_arn = rules.get('stream')
    if not trigger_arn:
        trigger_arn = rules.get('table')

    lambda_alias_arn = get_lambda_alias_arn(app=app_name, account=env, region=region)
    stream_arn = get_dynamodb_streams_arn(arn_string=trigger_arn, account=env, region=region)
    protocol = 'lambda'

    statement_id = '{}_dynamodb_{}'.format(app_name, trigger_arn)
    principal = 'dynamodb.amazonaws.com'
    add_lambda_permissions(
        function=lambda_alias_arn,
        statement_id=statement_id,
        action='lambda:InvokeFunction',
        principal=principal,
        source_arn=stream_arn,
        env=env,
        region=region)

    # TODO: Fix IAM permission, attached DynamoDB all to lambda function role
    source_exists = False
    event_sources = lambda_client.list_event_source_mappings(FunctionName=lambda_alias_arn)
    for each_source in event_sources['EventSourceMappings']:
        if each_source['EventSourceArn'] == stream_arn:
            source_exists = True
    if not source_exists:
        lambda_client.create_event_source_mapping(
            EventSourceArn=stream_arn,
            FunctionName=lambda_alias_arn,
            StartingPosition='TRIM_HORIZON')
        LOG.debug("DynamoDB Streams Lambda event created")
    else:
        LOG.debug("DynamoDB Streams Lambda event already existed, skipping readding")

    LOG.info("Created DynamoDB Streams event trigger on %s for %s", lambda_alias_arn, stream_arn)
