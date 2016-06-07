"""Post a message to slack."""
import logging

import slacker

LOG = logging.getLogger(__name__)

def post_slack_message(message, channel):
    """Format the message and post to the appropriate slack channel."""

    slack_token = 'xoxb-xxxxxxxxx'

    LOG.debug('Slack Channel: {}\nSlack Message: {}'.format(channel, message))
    slack = slacker.Slacker(slack_token)
    try:
        slack.chat.post_message(channel, message)
        LOG.info('Message posted to {}'.format(channel))
    except slacker.Error:
        LOG.info("error posted message to  {}".format(channel))
