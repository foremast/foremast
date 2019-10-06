"""dynamodb table stream functions."""
import logging

import boto3

from ..exceptions import DynamoDBStreamNotFound, DynamoDBTableNotFound

LOG = logging.getLogger(__name__)


def check_arn_type(arn_string):
    """Check ARN

    Args:
        arn_string (str): ARN String to check and validate

    Returns:
        str: ARN for requested table name

    """

    if arn_string.startswith('arn:aws:dynamodb:'):
        _prefix, table, *stream = arn_string.split('/')

        LOG.debug("ARN Split: %s %s %s", _prefix, table, stream)
        if stream:
            arn_type = "dynamodb-stream"
        elif table:
            arn_type = "dynamodb-table"
        else:
            raise Exception('ARN Type could not be determined from {0}. Check provided ARN String.'.format(arn_string))

    return arn_type


def lookup_latest_dynamodb_stream(account, region, arn_string=None, table_name=None):
    """Lookup dynamodb stream ARN by DynamoDB table arn or raw table name

    Args:
        account (str): Environment, e.g. dev
        region (str): Region name, e.g. us-east-1
        arn_string (str): DynamoDB ARN String to look for stream
        table_name (str): DynamoDB table name to look for stream

    Returns:
        str: ARN for latest DynamoDB stream ARN

    """
    session = boto3.Session(profile_name=account, region_name=region)
    dynamodb_client = session.client('dynamodb')
    dynamodb_streams_client = session.client('dynamodbstreams')

    if arn_string:
        _prefix, table_name, *stream = arn_string.split('/')
        LOG.info('DynamoDB Stream ARN provided. Looking up Table Name from: {0}'.format(arn_string))

    LOG.info('Checking DynamoDB Table Response of table {0}'.format(table_name))
    table_response = dynamodb_client.describe_table(TableName=table_name)

    if 'Table' not in table_response:
        LOG.critical("No DynamoDB table named %s was found.", table_name)
        raise DynamoDBTableNotFound('No DynamoDB table named {0} was found'.format(table_name))

    streams_response = dynamodb_streams_client.list_streams(TableName=table_name)
    streams = streams_response['Streams']

    # Return latest stream if exact stream not provided
    try:
        latest_stream_arn = streams[0]['StreamArn']
    except IndexError:
        LOG.critical("No DynamoDB stream found for table %s.", table_name)
        raise DynamoDBStreamNotFound('No DynamoDB stream found for table named {0}'.format(table_name))
    return latest_stream_arn


def get_dynamodb_stream_arn(arn_string, account, region):
    """Get DynamoDB stream ARN from a DynamoDB table.

    Args:
        arn_string (str): Name of the table stream to lookup a stream
        account (str): Environment, e.g. dev
        region (str): Region name, e.g. us-east-1

    Returns:
        str: ARN for requested table name

    """
    arn_type = check_arn_type(arn_string)

    if arn_type == 'dynamodb-stream':
        return arn_string
    elif arn_type == 'dynamodb-table':
        return lookup_latest_dynamodb_stream(account, region, arn_string=arn_string)
    return lookup_latest_dynamodb_stream(account, region, table_name=arn_string)
