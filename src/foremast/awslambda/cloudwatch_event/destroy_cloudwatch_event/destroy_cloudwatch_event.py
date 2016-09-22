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

"""Destroy any DNS records."""
import logging

import boto3

from ....utils.get_cloudwatch_event_rule import get_cloudwatch_event_rule

LOG = logging.getLogger(__name__)


def destroy_cloudwatch_event(app='', env='dev', region=''):
    """Destroy Cloudwatch event subscription.

    Args:
        app (str): Spinnaker Application name.
        env (str): Deployment environment.
        region (str): AWS region.
    Returns:
        bool: True upon successful completion.
    """

    session = boto3.Session(profile_name=env, region_name=region)
    cloudwatch_client = session.client('events')

    event_rules = get_cloudwatch_event_rule(app_name=app, account=env, region=region)

    for rule in event_rules:
        cloudwatch_client.remove_targets(
            Rule=rule,
            Ids=[app]
        )

    return True
