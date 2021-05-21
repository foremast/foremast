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
"""Post a message to slack."""
import logging

import slacker

from ..consts import SLACK_TOKEN

LOG = logging.getLogger(__name__)


def post_slack_message(message=None, channel=None, username=None, icon_emoji=None):
    """Format the message and post to the appropriate slack channel.

    Args:
        message (str): Message to post to slack
        channel (str): Desired channel. Must start with #

    """
    LOG.debug('Slack Channel: %s\nSlack Message: %s', channel, message)
    slack = slacker.Slacker(SLACK_TOKEN)
    try:
        slack.chat.post_message(channel=channel, text=message, username=username, icon_emoji=icon_emoji)
        LOG.info('Message posted to %s', channel)
    except slacker.Error:
        LOG.info("error posted message to %s", channel)
