#   Foremast - Pipeline Tooling
#
#   Copyright 2019 Redbox Automated Retail, LLC
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
"""Create Event Source Mapping trigger for lambda"""

import logging

import boto3

from ...utils import get_lambda_alias_arn, get_dynamodb_stream_arn
from ...exceptions import DynamoDBTableNotFound

LOG = logging.getLogger(__name__)


def create_event_source_mapping_trigger(app_name, env, region, event_source, rules):
    """Create event source mapping trigger from rules for AWS Lambda.

    Args:
        app_name (str): name of the lambda function
        env (str): Environment/Account for lambda function
        region (str): AWS region of the lambda function
        event_source (str): Event Source Service (DynamoDB, Kinesis, SQS)
        rules (str): Trigger rules from the settings
    """
    session = boto3.Session(profile_name=env, region_name=region)
    lambda_client = session.client('lambda')

    if event_source == 'DynamoDB':
        trigger_arn = rules.get('stream')
        if not trigger_arn:
            trigger_arn = rules.get('table')
            if not trigger_arn:
                raise DynamoDBTableNotFound

        source_arn = get_dynamodb_stream_arn(arn_string=trigger_arn, account=env, region=region)
    else:
        raise NotImplementedError
    lambda_alias_arn = get_lambda_alias_arn(app=app_name, account=env, region=region)

    event_sources = lambda_client.list_event_source_mappings(FunctionName=lambda_alias_arn)
    LOG.debug('Found event sources: {0}'.format(event_sources))

    for each_source in event_sources['EventSourceMappings']:
        if each_source['EventSourceArn'] == source_arn:
            event_uuid = each_source['UUID']
            lambda_client.update_event_source_mapping(
                UUID=event_uuid,
                FunctionName=lambda_alias_arn,
                BatchSize=rules.get('batch_size', 100),
                MaximumBatchingWindowInSeconds=rules.get('batch_window', 0))
            LOG.debug('{0} event trigger updated'.format(event_source))
            break
    else:
        lambda_client.create_event_source_mapping(
            EventSourceArn=source_arn,
            FunctionName=lambda_alias_arn,
            BatchSize=rules.get('batch_size', 100),
            MaximumBatchingWindowInSeconds=rules.get('batch_window', 0),
            StartingPosition=rules.get('starting_postion', 'TRIM_HORIZON'))
        LOG.debug('{0} event trigger created'.format(event_source))

    LOG.info('Created %s event trigger on %s for %s', event_source, lambda_alias_arn, source_arn)
