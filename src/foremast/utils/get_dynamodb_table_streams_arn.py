"""dynamodb table streams functions."""
import logging

import boto3

from ..exceptions import DynamoDBTableNotFound, DynamoDBStreamsNotFound

LOG = logging.getLogger(__name__)


def get_dynamodb_table_streams_arn(stream_name, account, region):
    """Get dynamodb table streams ARN.

    Args:
        stream_name (str): Name of the table stream to lookup a stream
        account (str): Environment, e.g. dev
        region (str): Region name, e.g. us-east-1

    Returns:
        str: ARN for requested table name

    """
    # Case where table stream is provided directly
    if stream_name.count(':') == 5 and stream_name.startswith('arn:aws:dynamodb:') and '/stream/' in stream_name:
        return stream_name

    # Case where Dynamo Table ARN Provided (and lookup still needed)
    if stream_name.count(':') == 5 and stream_name.startswith('arn:aws:dynamodb:') and ':table/' in stream_name:
        arn, table_name = stream_name.split(':table/')

    session = boto3.Session(profile_name=account, region_name=region)
    dynamodb_client = session.client('dynamodb')
    dynamodb_streams_client = session.client('dynamodbstreams')

    table_response = dynamodb_client.describe_table(TableName=table_name)
    table_info = table_response['Table']

    if not table_info:
        LOG.critical("No DynamoDB table named %s found.", table_name)
        raise DynamoDBTableNotFound('No DynamoDB table named {0} found'.format(table_name))

    streams_response = dynamodb_streams_client.list_streams(TableName=table_name)
    streams = streams_response['Streams']

    # Return latest stream if exact stream not provided
    if streams:
        latest_stream_arn = streams[0]
    else:
        LOG.critical("No DynamoDB table streams found for table %s.", table_name)
        raise DynamoDBStreamsNotFound('No DynamoDB table stream found for table named {0}'.format(table_name))
    return latest_stream_arn
