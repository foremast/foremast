"""dynamodb table functions."""
import logging

import boto3

from ..exceptions import DynamoDBTableNotFound

LOG = logging.getLogger(__name__)


def get_dynamodb_table_arn(table_name, account, region):
    """Get dynamodb table ARN.

    Args:
        table_name (str): Name of the table to lookup.
        account (str): Environment, e.g. dev
        region (str): Region name, e.g. us-east-1

    Returns:
        str: ARN for requested table name

    """
    if table_name.count(':') == 5 and table_name.startswith('arn:aws:dynamodb:'):
        return table_name
    session = boto3.Session(profile_name=account, region_name=region)
    dynamodb_client = session.client('dynamodb')

    tables = dynamodb_client.list_tables()['tables']

    matched_table = None
    for table in tables:
        table_arn = table['tableArn']
        if table_name == table_arn.split(':')[-1]:
            matched_table = table_arn
            break
    else:
        LOG.critical("No table with name %s found.", table_name)
        raise DynamoDBTableNotFound('No table with name {0} found'.format(table_name))
    return matched_table
