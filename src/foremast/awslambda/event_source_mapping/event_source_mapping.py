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

from ...exceptions import DynamoDBTableNotFound
from ...utils import get_dynamodb_stream_arn, get_lambda_alias_arn

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
    event_defaults = {
        'dynamodb-stream': {
            'service_name': 'DynamoDB Stream',
            'batch_size': 100,
            'batch_window': 0,
            'starting_position': 'TRIM_HORIZON',
            'split_on_error': False,
            'max_retry_attempts': 10000,
            'destination_config': {},
            'max_record_age': 604800
        },
        'kinesis-stream': {
            'service_name': 'Kinesis Stream',
            'batch_size': 100,
            'batch_window': 0,
            'starting_position': 'TRIM_HORIZON',
            'split_on_error': False,
            'max_retry': 10000,
            'destination_config': {},
            'max_record_age': 604800
        },
        'sqs': {
            'service_name': 'SQS Queue',
            'batch_size': 10
        }
    }

    if event_source == 'dynamodb-stream':
        trigger_arn = rules.get('stream_arn')
        if not trigger_arn:
            trigger_arn = rules.get('table_arn')
            if not trigger_arn:
                raise DynamoDBTableNotFound

        event_source_arn = get_dynamodb_stream_arn(arn_string=trigger_arn, account=env, region=region)
    elif event_source == 'kinesis-stream':
        event_source_arn = rules.get('stream_arn')
    elif event_source == 'sqs':
        event_source_arn = rules.get('queue_arn')
    else:
        raise NotImplementedError

    lambda_alias_arn = get_lambda_alias_arn(app=app_name, account=env, region=region)

    event_sources = lambda_client.list_event_source_mappings(FunctionName=lambda_alias_arn)
    LOG.debug('Found event sources: {0}'.format(event_sources))

    for each_source in event_sources['EventSourceMappings']:
        if each_source['EventSourceArn'] == event_source_arn and (
                event_source == 'dynamodb-stream' or event_source == 'kinesis-stream'):
            event_uuid = each_source['UUID']
            lambda_client.update_event_source_mapping(
                UUID=event_uuid,
                FunctionName=lambda_alias_arn,
                BatchSize=rules.
                get('batch_size', event_defaults[event_source]['batch_size']),
                MaximumBatchingWindowInSeconds=rules.
                get('batch_window', event_defaults[event_source]['batch_window']),
                BisectBatchOnFunctionError=rules.
                get('split_on_error', event_defaults[event_source]['split_on_error']),
                MaximumRetryAttempts=rules.
                get('max_retry', event_defaults[event_source]['max_retry']),
                DestinationConfig=rules.
                get('destination_config', event_defaults[event_source]['destination_config']),
                MaximumRecordAgeInSeconds=rules.
                get('max_record_age', event_defaults[event_source]['max_record_age']))
            LOG.debug('{0} event trigger updated'.format(event_defaults[event_source]['service_name']))
            break
        else:
            event_uuid = each_source['UUID']
            lambda_client.update_event_source_mapping(
                UUID=event_uuid,
                FunctionName=lambda_alias_arn,
                BatchSize=rules.get('batch_size', event_defaults[event_source]['batch_size']))
            LOG.debug('{0} event trigger updated'.format(event_defaults[event_source]['service_name']))
            break
    else:
        if event_source == 'sqs':
            lambda_client.create_event_source_mapping(
                EventSourceArn=event_source_arn,
                FunctionName=lambda_alias_arn,
                BatchSize=rules.get('batch_size', event_defaults[event_source]['batch_size']))
        else:
            lambda_client.create_event_source_mapping(
                EventSourceArn=event_source_arn,
                FunctionName=lambda_alias_arn,
                BatchSize=rules.
                get('batch_size', event_defaults[event_source]['batch_size']),
                MaximumBatchingWindowInSeconds=rules.
                get('batch_window', event_defaults[event_source]['batch_window']),
                StartingPosition=rules.
                get('starting_position', event_defaults[event_source]['starting_position']),
                BisectBatchOnFunctionError=rules.
                get('split_on_error', event_defaults[event_source]['split_on_error']),
                MaximumRetryAttempts=rules.
                get('max_retry', event_defaults[event_source]['max_retry']),
                DestinationConfig=rules.
                get('destination_config', event_defaults[event_source]['destination_config']),
                MaximumRecordAgeInSeconds=rules.
                get('max_record_age', event_defaults[event_source]['max_record_age']))
        LOG.debug('{0} event trigger created'.format(event_defaults[event_source]['service_name']))

    LOG.info('Created {} event trigger on {} for {}'.format(event_defaults[event_source]['service_name'],
                                                            lambda_alias_arn, event_source_arn))
