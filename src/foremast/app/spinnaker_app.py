"""Base App."""
import copy
import logging

from pprint import pformat
from ..consts import LINKS
from ..exceptions import ForemastError
from ..utils import get_template, wait_for_task
from ..utils.gate import gate_request


# pylint: disable=abstract-method
class SpinnakerApp:
    """Base App."""

    def __init__(self, provider, pipeline_config=None, app=None, email=None, project=None, repo=None):
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
            'provider': provider
        }

        self.appname = app
        self.pipeline_config = pipeline_config

    def create(self):
        """Send a POST to spinnaker to create a new application with class variables.

                Raises:
                    AssertionError: Application creation failed.

                """

        # Retaining abstract account list for backwards compatibility
        # Refer to #366
        self.appinfo['accounts'] = ['default']
        self.log.debug('Pipeline Config\n%s', pformat(self.pipeline_config))
        self.log.debug('App info:\n%s', pformat(self.appinfo))
        jsondata = self.render_application_template()
        wait_for_task(jsondata)

        self.log.info("Successfully created %s application", self.appname)
        return jsondata

    def render_application_template(self):
        """Render application from configs.

        Returns:
            dict: Rendered application template.
        """
        self.pipeline_config['instance_links'] = self.retrieve_instance_links()
        jsondata = get_template(
            template_file='infrastructure/app_data.json.j2', appinfo=self.appinfo, pipeline_config=self.pipeline_config)
        return jsondata

    def retrieve_instance_links(self):
        """Combine default and configuration instance links.

        Returns:
            dict: Combined instance links.
        """
        instance_links = copy.copy(LINKS)
        self.log.debug('Default instance links: %s', instance_links)
        instance_links.update(self.pipeline_config['instance_links'])
        self.log.debug('Updated instance links: %s', instance_links)

        return instance_links

    def get_accounts(self):
        """Get Accounts added to Spinnaker.

        Returns:
            list: list of dicts of Spinnaker credentials matching _provider_.

        Raises:
            AssertionError: Failure getting accounts from Spinnaker.
        """
        uri = '/credentials'
        response = gate_request(uri=uri)
        assert response.ok, 'Failed to get accounts: {0}'.format(response.text)

        all_accounts = response.json()
        self.log.debug('Accounts in Spinnaker:\n%s', all_accounts)

        filtered_accounts = []
        for account in all_accounts:
            if account['type'] == self.provider:
                filtered_accounts.append(account)

        if not filtered_accounts:
            raise ForemastError('No Accounts matching {0}.'.format(self.provider))

        return filtered_accounts
