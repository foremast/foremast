"""Base App."""
import copy
import logging

from ..common.base import BasePlugin
from ..consts import LINKS
from ..exceptions import ForemastError
from ..utils import get_template
from ..utils.gate import gate_request


# pylint: disable=abstract-method
class BaseApp(BasePlugin):
    """Base App."""

    resource = 'app'

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

    def get_accounts(self, provider='aws'):
        """Get Accounts added to Spinnaker.

        Args:
            provider (str): What provider to find accounts for.

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
            if account['type'] == provider:
                filtered_accounts.append(account)

        if not filtered_accounts:
            raise ForemastError('No Accounts matching {0}.'.format(provider))

        return filtered_accounts
