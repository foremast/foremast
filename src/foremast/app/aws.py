"""AWS Spinnaker Application."""
from pprint import pformat

from foremast.app import base
from foremast.utils import wait_for_task


class SpinnakerApp(base.BaseApp):
    """Create AWS Spinnaker Application."""

    provider = 'aws'

    def create(self):
        """Send a POST to spinnaker to create a new application with class variables.

        Raises:
            AssertionError: Application creation failed.

        """
        self.appinfo['accounts'] = self.get_accounts()
        self.log.debug('Pipeline Config\n%s', pformat(self.pipeline_config))
        self.log.debug('App info:\n%s', pformat(self.appinfo))
        jsondata = self.retrieve_template()
        wait_for_task(jsondata)

        self.log.info("Successfully created %s application", self.appname)
        return

    def delete(self):
        """Delete AWS Spinnaker Application."""
        return False

    def update(self):
        """Update AWS Spinnaker Application."""
        return False
