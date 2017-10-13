"""AWS Spinnaker Application."""
import logging
from pprint import pformat
from foremast.app.base import BaseApp
from foremast.utils import wait_for_task


class SpinnakerApp(BaseApp):
    """Create AWS Spinnaker Application."""

    def __init__(self, pipeline_config=None, app=None, email=None, project=None, repo=None):
        """Class to manage and create Spinnaker applications

        Args:
            pipeline_config (dict): pipeline.json data.
            app (str): Application name.
            email (str): Email associated with application.
            project (str): Git namespace or project group
            repo (str): Repository name

        """
        self.log = logging.getLogger(__name__)

        self.appinfo = {
            'app': app,
            'email': email,
            'project': project,
            'repo': repo,
        }
        self.appname = app
        self.pipeline_config = pipeline_config

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
