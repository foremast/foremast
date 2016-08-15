"""Destroy S3 events."""
import logging

import boto3

LOG = logging.getLogger(__name__)


def destroy_s3_event(app, env, region):
    """Destroy S3 event.

    Args:
        app (str): Spinnaker Application name.
        env (str): Deployment environment.
        region (str): AWS region.
    Returns:
        bool: True upon successful completion.
    """

    # TODO: how do we know which bucket to process if triggers dict is empty?
    # Maybe list buckets and see which has notification to that lambda defined?
    # TODO: buckets should be named the same as apps, what if one app has multiple buckets?
    # bucket = rules.get('bucket')
    bucket = "{0}-{1}-{2}".format('gogo', app, env)

    session = boto3.Session(profile_name=env, region_name=region)
    s3_client = session.client('s3')

    config = {}

    s3_client.put_bucket_notification_configuration(Bucket=bucket, NotificationConfiguration=config)
    LOG.debug("Deleted Lambda S3 notification")

    return True
