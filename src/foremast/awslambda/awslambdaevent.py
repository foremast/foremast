"""Creates Lambda event triggers."""
import logging

from foremast.utils import get_properties
from .s3_event import create_s3_event
from .sns_event import create_sns_event
from .cloudwatch_event import create_cloudwatch_event
from .cloudwatch_log_event.cloudwatch_log_event import create_cloudwatch_log_event

LOG = logging.getLogger(__name__)


class LambdaEvent(object):
    """
    Manipulate Lambda events
    """
    def __init__(self, app=None, env=None, region=None, prop_path=None):
        """
        Lambda event object
        Args:
            app (str): Application name
            env (str): Environment/Account
            region (str): AWS Region
            prop_path (str): Path of environment property file
        """
        self.log = logging.getLogger(__name__)

        self.app_name = app
        self.env = env
        self.region = region
        self.properties = get_properties(properties_file=prop_path, env=env)

    def create_lambda_events(self):
        """
        Creates all defined lambda events for an lambda application
        Returns:
             boolean: True if all events are created

        """
        triggers = self.properties['triggers']
        for trigger in triggers:
            if trigger['type'] == 's3':
                if create_s3_event(app_name=self.app_name, env=self.env, region=self.region, rules=trigger):
                    LOG.info("Created lambda %s S3 event on bucket %s", self.app_name, trigger['bucket'])
            if trigger['type'] == 'sns':
                if create_sns_event(app_name=self.app_name, env=self.env, region=self.region, rules=trigger):
                    LOG.info("Created SNS event subscription on topic %s", trigger['topic'])

            if trigger['type'] == 'cloudwatch-event':
                if create_cloudwatch_event(app_name=self.app_name, env=self.env, region=self.region, rules=trigger):
                    LOG.info("Created Cloudwatch event with schedule: %s", trigger['schedule'])

            if trigger['type'] == 'cloudwatch-logs':
                if create_cloudwatch_log_event(app_name=self.app_name, env=self.env, region=self.region, rules=trigger):
                    LOG.info("Created Cloudwatch log event with filter: %s", trigger['filter_pattern'])
        else:
            LOG.debug("Defined triggers: {}", triggers)
            LOG.info("No lambda events created")
