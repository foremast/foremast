#   Foremast - Pipeline Tooling
#
#   Copyright 2016 Gogo, LLC
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

import logging
import json

import boto3

from ...exceptions import InvalidEventConfiguration
from ...utils import (get_template, get_lambda_alias_arn, add_lambda_permissions)

LOG = logging.getLogger(__name__)


def create_s3_event(app_name, env, region, rules):
    """Create S3 lambda event from rules.

    Args:
        app_name (str): name of the lambda function
        env (str): Environment/Account for lambda function
        region (str): AWS region of the lambda function
        rules (str): Trigger rules from the settings
    """

    session = boto3.Session(profile_name=env, region_name=region)
    s3_client = session.client('s3')

    bucket = rules.get('bucket')
    events = rules.get('events')
    prefix = rules.get('prefix')
    suffix = rules.get('suffix')

    lambda_alias_arn = get_lambda_alias_arn(app_name, env, region)

    LOG.debug("Lambda ARN for lambda function %s is %s.", app_name, lambda_alias_arn)
    LOG.debug("Creating S3 event for bucket %s with events %s", bucket, events)

    if None in (bucket, events):
        LOG.critical("Bucket and events have to be defined")
        raise InvalidEventConfiguration("Bucket and events have to be defined")

    filters = []

    if prefix:
        prefix_dict = {"Name": "prefix", "Value": prefix}
        filters.append(prefix_dict)

    if suffix:
        suffix_dict = {"Name": "suffix", "Value": suffix}
        filters.append(suffix_dict)

    if filters:
        json_filters = json.dumps(filters)
    else:
        json_filters = None

    template_kwargs = {"lambda_arn": lambda_alias_arn, "events": json.dumps(events), "filters": json_filters}

    config = get_template(template_file='infrastructure/lambda/s3_event.json.j2', **template_kwargs)

    principal = 's3.amazonaws.com'
    statement_id = "{}_s3_{}".format(app_name, bucket)
    source_arn = "arn:aws:s3:::{}".format(bucket)
    add_lambda_permissions(function=lambda_alias_arn,
                           env=env,
                           region=region,
                           principal=principal,
                           statement_id=statement_id,
                           source_arn=source_arn)

    s3_client.put_bucket_notification_configuration(Bucket=bucket, NotificationConfiguration=json.loads(config))
    LOG.info("Created lambda %s S3 event on bucket %s", app_name, bucket)
