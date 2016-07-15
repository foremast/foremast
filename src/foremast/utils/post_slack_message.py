"""Post a message to slack."""
import logging

import slacker

from config_loader import get_configs

LOG = logging.getLogger(__name__)


def post_slack_message(message, channel):
    """Format the message and post to the appropriate slack channel.

    Args:
        message (str): Message to post to slack
        channel (str): Desired channel. Must start with #
    """

    slack_token = get_configs(section='credentials')['slack_token']
    print(slack_token)
    LOG.debug('Slack Channel: %s\nSlack Message: %s', channel, message)
    slack = slacker.Slacker(slack_token)
    try:
        slack.chat.post_message(channel, message)
        LOG.info('Message posted to %s', channel)
    except slacker.Error:
        LOG.info("error posted message to %s", channel)

post_slack_message("test", "@dcampbell")
