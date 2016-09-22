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

"""Destroy any cloudwatch log events."""
import logging

import boto3

LOG = logging.getLogger(__name__)


def destroy_cloudwatch_log_event(app='', env='dev', region=''):
    """Destroy Cloudwatch log event.

    Args:
        app (str): Spinnaker Application name.
        env (str): Deployment environment.
        region (str): AWS region.
    Returns:
        bool: True upon successful completion.
    """

    session = boto3.Session(profile_name=env, region_name=region)
    cloudwatch_client = session.client('logs')

    # FIXME: see below
    # TODO: Log group name is required, where do we get it if it is not in application-master-env.json?
    cloudwatch_client.delete_subscription_filter(
        logGroupName='/aws/lambda/awslimitchecker',
        filterName=app
    )

    return True
