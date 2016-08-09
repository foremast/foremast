import boto3
import logging

LOG = logging.getLogger(__name__)


class LambdaFunctionDoesNotExist(Exception):
    pass


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
            LOG.debug("Lambda ARN for lambda function {0} is {1}.".format(app, lambda_arn))
            return lambda_arn
    else:
        LOG.fatal('Lambda function with name {0} not found in {1} {2}'.format(app, account, region))
        raise LambdaFunctionDoesNotExist('Lambda function with name {0} not found in {1} {2}'.format(app,
                                                                                                     account,
                                                                                                     region))
