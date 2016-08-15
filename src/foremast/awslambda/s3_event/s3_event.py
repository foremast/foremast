import logging
import json

import boto3

from ...exceptions import InvalidEventConfiguration
from ...utils import (get_template, get_lambda_arn)

LOG = logging.getLogger(__name__)


def create_s3_event(app_name, env, region, rules):
    """Creates S3 lambda event from rules"""

    session = boto3.Session(profile_name=env, region_name=region)
    s3_client = session.client('s3')

    bucket = rules.get('bucket')
    events = rules.get('events')
    prefix = rules.get('prefix')
    suffix = rules.get('suffix')

    lambda_arn = get_lambda_arn(app_name, env, region)

    LOG.debug("Lambda ARN for lambda function %s is %s.", app_name, lambda_arn)
    LOG.debug("Creating S3 event for bucket %s with events %s", bucket, events)

    if None in (bucket, events):
        LOG.critical("Bucket and events have to be defined")
        raise InvalidEventConfiguration("Bucket and events have to be defined")

    filters = []

    if prefix:
        prefix_dict = {
            "Name": "prefix",
            "Value": prefix
        }
        filters.append(prefix_dict)

    if suffix:
        suffix_dict = {
            "Name": "suffix",
            "Value": suffix
        }
        filters.append(suffix_dict)

    template_kwargs = {
        "lambda_arn": lambda_arn,
        "events": json.dumps(events),
        "filters": json.dumps(filters)
    }

    config = get_template(template_file='infrastructure/lambda/s3_event.json.j2', **template_kwargs)

    s3_client.put_bucket_notification_configuration(Bucket=bucket,
                                                    NotificationConfiguration=json.loads(config))
    LOG.info("Created lambda %s S3 event on bucket %s", app_name, bucket)
