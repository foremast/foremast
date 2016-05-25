"""Posts a message to slack"""
import logging

from slacker import Slacker 

LOG = logging.getLogger(__name__)

def post_slack_message(message, channel):
    """ formats the message and posts to the appropriate slack channel """

    slack_token = 'xoxb-xxxxxxxxx'

    LOG.debug('Slack Channel: {}\nSlack Message: {}'.format(channel, message)) 
    slack = Slacker(slack_token)
    slack.chat.post_message(channel, message)
    LOG.info('Message posted to {}'.format(channel))
