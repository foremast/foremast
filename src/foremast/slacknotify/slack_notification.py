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
"""Notify Slack channel."""
import time

from ..utils import get_properties, get_template, post_slack_message


class SlackNotification:
    """Post slack notification.
    Inform users about infrastructure changes to prod* accounts.

    Args:
        app (str): Application name
        env (str): Environment/account name of changed infrastructure
        prop_path (str): Path to the rendered configuration files
    """

    def __init__(self, app=None, env=None, prop_path=None):
        timestamp = time.strftime("%B %d, %Y %H:%M:%S %Z", time.gmtime())

        self.settings = get_properties(prop_path)
        short_commit_sha = self.settings['pipeline']['config_commit'][0:11]

        self.info = {
            'app': app,
            'env': env,
            'config_commit_short': short_commit_sha,
            'timestamp': timestamp,
        }

    def post_message(self):
        """Send templated message to **#deployments-{env}**.

        Primarily for production deployments.
        """
        message = get_template(template_file='slack/pipeline-prepare-ran.j2', info=self.info)
        channel = '#deployments-prod'
        post_slack_message(message=message, channel=channel, username='pipeline-bot', icon_emoji=':gear:')

    def notify_slack_channel(self):
        """Post message to a defined Slack channel."""
        message = get_template(template_file='slack/pipeline-prepare-ran.j2', info=self.info)

        if self.settings['pipeline']['notifications']['slack']:
            post_slack_message(
                message=message,
                channel=self.settings['pipeline']['notifications']['slack'],
                username='pipeline-bot',
                icon_emoji=':gear:')
