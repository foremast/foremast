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
"""Create S3 lambda event"""

import json
import logging

import boto3

from ...utils import add_lambda_permissions, get_lambda_alias_arn, get_template

LOG = logging.getLogger(__name__)


def create_s3_event(app_name, env, region, bucket, triggers):
    """Create S3 lambda events from triggers

    Args:
        app_name (str): name of the lambda function
        env (str): Environment/Account for lambda function
        region (str): AWS region of the lambda function
        triggers (list): List of triggers from the settings
    """
    session = boto3.Session(profile_name=env, region_name=region)
    s3_client = session.client('s3')

    lambda_alias_arn = get_lambda_alias_arn(app_name, env, region)

    LOG.debug("Lambda ARN for lambda function %s is %s.", app_name, lambda_alias_arn)
    LOG.debug("Creating S3 events for bucket %s", bucket)

    # allow lambda trigger permission from bucket
    principal = 's3.amazonaws.com'
    statement_id = "{}_s3_{}".format(app_name, bucket).replace('.', '')
    source_arn = "arn:aws:s3:::{}".format(bucket)
    add_lambda_permissions(
        function=lambda_alias_arn,
        env=env,
        region=region,
        principal=principal,
        statement_id=statement_id,
        source_arn=source_arn)

    # configure events on s3 bucket to trigger lambda function
    template_kwargs = {"lambda_arn": lambda_alias_arn, "triggers": triggers}
    config = get_template(template_file='infrastructure/lambda/s3_event.json.j2', **template_kwargs)
    s3_client.put_bucket_notification_configuration(Bucket=bucket, NotificationConfiguration=json.loads(config))

    LOG.info("Created lambda %s S3 event on bucket %s", app_name, bucket)
