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
"""Create Lambda event triggers."""
from ..utils import get_properties, remove_all_lambda_permissions
from .api_gateway_event import APIGateway
from .cloudwatch_event import create_cloudwatch_event
from .cloudwatch_log_event import create_cloudwatch_log_event
from .event_source_mapping import create_event_source_mapping_trigger
from .s3_event import create_s3_event
from .sns_event import create_sns_event


# pylint: disable=too-few-public-methods
class LambdaEvent:
    """Manipulate Lambda events."""

    def __init__(self, app=None, env=None, region=None, prop_path=None):
        """Lambda event object.

        Args:
            app (str): Application name
            env (str): Environment/Account
            region (str): AWS Region
            prop_path (str): Path of environment property file
        """
        self.app_name = app
        self.env = env
        self.region = region
        self.prop_path = prop_path
        self.properties = get_properties(properties_file=prop_path, env=env, region=region)

    def create_lambda_events(self):
        """Create all defined lambda events for an lambda application."""

        # Clean up lambda permissions before creating triggers
        remove_all_lambda_permissions(app_name=self.app_name, env=self.env, region=self.region)

        triggers = self.properties['lambda_triggers']

        for trigger in triggers:
            if trigger['type'] == 'api-gateway':
                apigateway = APIGateway(
                    app=self.app_name, env=self.env, region=self.region, rules=trigger, prop_path=self.prop_path)
                apigateway.setup_lambda_api()

            if trigger['type'] == 'cloudwatch-event':
                create_cloudwatch_event(app_name=self.app_name, env=self.env, region=self.region, rules=trigger)

            if trigger['type'] == 'cloudwatch-logs':
                create_cloudwatch_log_event(app_name=self.app_name, env=self.env, region=self.region, rules=trigger)

            if trigger['type'] in ['dynamodb-stream', 'kinesis-stream', 'sqs']:
                create_event_source_mapping_trigger(app_name=self.app_name, env=self.env, region=self.region,
                                                    event_source=trigger['type'], rules=trigger)

            if trigger['type'] == 'sns':
                create_sns_event(app_name=self.app_name, env=self.env, region=self.region, rules=trigger)

        # filter all triggers to isolate s3 triggers so we can operate on the entire group
        s3_triggers = [x for x in triggers if x['type'] == 's3']

        # group triggers by unique target bucket
        bucket_triggers = dict()
        for s3_trigger in s3_triggers:
            bucket = s3_trigger.get('bucket')
            if bucket in bucket_triggers:
                bucket_triggers[bucket].append(s3_trigger)
            else:
                bucket_triggers[bucket] = [s3_trigger]

        # apply relevant triggers to each respective bucket all at once.
        for bucket, triggers in bucket_triggers.items():
            create_s3_event(app_name=self.app_name, env=self.env, region=self.region, bucket=bucket, triggers=triggers)
