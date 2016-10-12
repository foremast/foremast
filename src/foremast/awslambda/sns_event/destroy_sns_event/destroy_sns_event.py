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

import boto3

from ....utils.get_sns_subscriptions import get_sns_subscriptions

LOG = logging.getLogger(__name__)


def destroy_sns_event(app_name, env, region):
    """ Destroy all Lambda SNS subscriptions.

    Args:
        app_name (str): name of the lambda function
        env (str): Environment/Account for lambda function
        region (str): AWS region of the lambda function

    Returns:
        boolean: True if subscription destroyed successfully
    """
    session = boto3.Session(profile_name=env, region_name=region)
    sns_client = session.client('sns')

    lambda_subscriptions = get_sns_subscriptions(app_name=app_name, env=env, region=region)

    for subscription_arn in lambda_subscriptions:
        sns_client.unsubscribe(
            SubscriptionArn=subscription_arn
        )

    LOG.debug("Lambda SNS event deleted")
    return True
