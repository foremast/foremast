import logging
import boto3

from ...utils import get_template
from ...utils.get_lambda_arn import get_lambda_arn
from ...utils.lambda_event_exception import InvalidEventConfiguration

LOG = logging.getLogger(__name__)


def create_s3_event(app_name, env, region, rules):
    """ Creates S3 lambda event from rules

    Returns:
        boolean: True if event created successfully
    """
    session = boto3.Session(profile_name=env, region_name=region)
    s3_client = session.client('s3')

    bucket = rules.get('bucket')
    events = rules.get('events')
    prefix = rules.get('prefix')
    suffix = rules.get('suffix')

    lambda_arn = get_lambda_arn(app_name, env, region)

    LOG.debug("Lambda ARN for lambda function %s is %s.", app_name, lambda_arn)
    LOG.debug("Creating S3 event for bucket %s with events %s", bucket, events)

    if bucket is None or events is None:
        LOG.critical("Bucket and events have to be defined")
        raise InvalidEventConfiguration("Bucket and events have to be defined")

    filters = []

    if prefix is not None:
        prefix_dict = {
           "type": "prefix",
           "value": prefix
        }
        filters.append(prefix_dict)

    if suffix is not None:
        suffix_dict = {
           "type": "suffix",
           "value": suffix
        }
        filters.append(suffix_dict)

    template_kwargs = {
        "lambda_arn": lambda_arn,
        "events": events,
        "bucket_name": bucket,
        "filters": filters
    }

    config = get_template(template_file='infrastructure/lambda/s3_event.json.j2', **template_kwargs)

    s3_client.put_bucket_notification_configuration(Bucket=bucket,
                                                    NotificationConfiguration=config)
    return True
