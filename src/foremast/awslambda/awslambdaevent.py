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

"""Create Lambda event triggers."""
import logging

from foremast.utils import get_properties

from .api_gateway_event import APIGateway
from .cloudwatch_event import create_cloudwatch_event
from .cloudwatch_log_event import create_cloudwatch_log_event
from .s3_event import create_s3_event
from .sns_event import create_sns_event


class LambdaEvent(object):
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
        self.properties = get_properties(properties_file=prop_path, env=env)

    def create_lambda_events(self):
        """Create all defined lambda events for an lambda application."""
        triggers = self.properties['lambda_triggers']

        for trigger in triggers:
            if trigger['type'] == 's3':
                create_s3_event(app_name=self.app_name, env=self.env, region=self.region, rules=trigger)

            if trigger['type'] == 'sns':
                create_sns_event(app_name=self.app_name, env=self.env, region=self.region, rules=trigger)

            if trigger['type'] == 'cloudwatch-event':
                create_cloudwatch_event(app_name=self.app_name, env=self.env, region=self.region, rules=trigger)

            if trigger['type'] == 'cloudwatch-logs':
                create_cloudwatch_log_event(app_name=self.app_name, env=self.env, region=self.region, rules=trigger)

            if trigger['type'] == 'api-gateway':
                apigateway = APIGateway(app=self.app_name, env=self.env, region=self.region, rules=trigger,
                                        prop_path=self.prop_path)
                apigateway.setup_lambda_api()
