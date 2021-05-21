#   Foremast - Pipeline Tooling
#
#   Copyright 2018 Gogo, LLC
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
"""Destroy S3 events."""
import logging

import boto3

from ....utils import get_details

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
    generated = get_details(app=app, env=env)

    bucket = generated.s3_app_bucket()

    session = boto3.Session(profile_name=env, region_name=region)
    s3_client = session.client('s3')

    config = {}

    s3_client.put_bucket_notification_configuration(Bucket=bucket, NotificationConfiguration=config)
    LOG.debug("Deleted Lambda S3 notification")

    return True
