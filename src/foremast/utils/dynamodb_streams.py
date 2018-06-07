"""dynamodb table streams functions."""
import logging

import boto3

from ..exceptions import DynamoDBTableNotFound, DynamoDBStreamsNotFound

LOG = logging.getLogger(__name__)


def check_arn_type(arn_string):
    """Check ARN

    Args:
        arn_string (str): ARN String to check and validate

    Returns:
        str: ARN for requested table name

    """
    arn_type = None

    if arn_string.count(':') >= 5 and arn_string.startswith('arn:aws:dynamodb:'):
        if '/stream/' in arn_string:
            arn_type = "dynamodb-streams"
        elif ':table/' in arn_string:
            arn_type = "dynamodb-table"
    return arn_type


def lookup_latest_dynamodb_stream(account, region, arn_string=None, table_name=None):
    """Lookup dynamodb streams ARN by DynamoDB table arn or raw table name

    Args:
        account (str): Environment, e.g. dev
        region (str): Region name, e.g. us-east-1
        arn_string (str): DynamoDB ARN String to look for streams
        table_name (str): DynamoDB table name to look for streams

    Returns:
        str: ARN for latest DynamoDB stream ARN

    """
    session = boto3.Session(profile_name=account, region_name=region)
    dynamodb_client = session.client('dynamodb')
    dynamodb_streams_client = session.client('dynamodbstreams')

    if arn_string:
        table_name = arn_string.split(':')[-1].split('table/')[-1]
    LOG.info(table_name)
    table_response = dynamodb_client.describe_table(TableName=table_name)
    table_info = table_response['Table']

    if not table_info:
        LOG.critical("No DynamoDB table named %s found.", table_name)
        raise DynamoDBTableNotFound('No DynamoDB table named {0} found'.format(table_name))

    streams_response = dynamodb_streams_client.list_streams(TableName=table_name)
    streams = streams_response['Streams']

    # Return latest stream if exact stream not provided
    try:
        latest_stream_arn = streams[0]['StreamArn']
    except IndexError:
        LOG.critical("No DynamoDB streams found for table %s.", table_name)
        raise DynamoDBStreamsNotFound('No DynamoDB streams found for table named {0}'.format(table_name))
    return latest_stream_arn


def get_dynamodb_streams_arn(arn_string, account, region):
    """Get DynamoDB streams ARN from a DynamoDB table.

    Args:
        arn_string (str): Name of the table stream to lookup a stream
        account (str): Environment, e.g. dev
        region (str): Region name, e.g. us-east-1

    Returns:
        str: ARN for requested table name

    """
    arn_type = check_arn_type(arn_string)

    if arn_type == 'dynamodb-streams':
        return arn_string
    elif arn_type == 'dynamodb-table':
        return lookup_latest_dynamodb_stream(account, region, arn_string=arn_string)
    return lookup_latest_dynamodb_stream(account, region, table_name=arn_string)
