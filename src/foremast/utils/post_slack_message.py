"""Post a message to slack."""
import logging

import slacker

from ..consts import SLACK_TOKEN

LOG = logging.getLogger(__name__)


def post_slack_message(message, channel):
    """Format the message and post to the appropriate slack channel.

    Args:
        message (str): Message to post to slack
        channel (str): Desired channel. Must start with #
    """

    LOG.debug('Slack Channel: %s\nSlack Message: %s', channel, message)
    slack = slacker.Slacker(SLACK_TOKEN)
    try:
        slack.chat.post_message(channel, message)
        LOG.info('Message posted to %s', channel)
    except slacker.Error:
        LOG.info("error posted message to %s", channel)

