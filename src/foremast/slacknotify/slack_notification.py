import logging
import time

from ..utils import get_template, get_properties, post_slack_message


class SlackNotification:
    """ Posts slack notification with information about infrastructure changes to prod* accounts """
    def __init__(self, info=None):
        self.info = info
        timestamp = time.strftime("%B %d, %Y %H:%M:%S %Z", time.gmtime())
        self.info['timestamp'] = timestamp
        self.settings = get_properties(self.info['properties'])
        self.info['config_commit_short'] = self.settings['pipeline']['config_commit'][0:11] 

    def post_message(self):
        message = get_template(
                  template_file='slack-templates/pipeline-prepare-ran.j2',
                  info=self.info)
        channel = '#deployments-{}'.format(self.info['env'].lower())
        post_slack_message(message, channel)
        #also posts message to defined slack channel
        if self.settings['pipeline']['notifications']['slack']:
            post_slack_message(message, self.settings['pipeline']['notifications']['slack'])

