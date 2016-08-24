import boto3
import logging

from ..exceptions import LambdaFunctionDoesNotExist

LOG = logging.getLogger(__name__)


def get_lambda_arn(app, account, region):
    """Get lambda ARN

    Args:
        account (str): AWS account name.
        region (str): Region name, e.g. us-east-1
        app (str): Lambda function name

    Returns:
        str: ARN for requested lambda function
    """
    session = boto3.Session(profile_name=account, region_name=region)
    lambda_client = session.client('lambda')

    lambda_functions = lambda_client.list_functions()['Functions']

    for lambda_function in lambda_functions:
        if lambda_function['FunctionName'] == app:
            lambda_arn = lambda_function['FunctionArn']
            LOG.debug("Lambda ARN for lambda function %s is %s.", app, lambda_arn)
            return lambda_arn
    else:
        LOG.fatal('Lambda function with name %s not found in %s %s', app, account, region)
        raise LambdaFunctionDoesNotExist('Lambda function with name {0} not found in {1} {2}'.format(app, account,
                                                                                                     region))


def add_lambda_permissions(function='',
                           statement_id='',
                           action='lambda:InvokeFunction',
                           principal='',
                           source_arn=None,
                           env='',
                           region='us-east-1'):
    """Add permission to Lambda for the event trigger.

    Args:
        function (str): Lambda function name
        action (str): Lambda action to allow
        principal (str): AWS principal to add permissions
        source_arn (str): ARN of the source of the event. Only needed for S3
        env (str): Environment/account of function
        region (str): AWS region of function
    """
    session = boto3.Session(profile_name=env, region_name=region)
    lambda_client = session.client('lambda')
    response_action = None
    try:
        if not source_arn:
            lambda_client.add_permission(FunctionName=function,
                                         StatementId=statement_id,
                                         Action=action,
                                         Principal=principal)
        else:
            lambda_client.add_permission(FunctionName=function,
                                         StatementId=statement_id,
                                         Action=action,
                                         Principal=principal,
                                         SourceArn=source_arn)
        response_action = 'Add permission with Sid: {}'.format(statement_id)
    except boto3.exceptions.botocore.exceptions.ClientError:
        response_action = "Did not add permissions"

    LOG.debug('Related StatementId (SID): %s', statement_id)
    LOG.info(response_action)
