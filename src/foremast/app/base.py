"""Base App."""
import logging
from pprint import pformat

import requests

from ..common.base import BasePlugin
from ..consts import API_URL, GATE_CA_BUNDLE, GATE_CLIENT_CERT, LINKS
from ..exceptions import ForemastError
from ..utils import get_template


# pylint: disable=abstract-method
class BaseApp(BasePlugin):
    """Base App."""

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

    def retrieve_template(self):
        """Sets the instance links with pipeline_configs and then renders template files

        Returns:
            jsondata: A json objects containing templates
        """
        links = self.retrieve_instance_links()
        self.log.debug('Links is \n%s', pformat(links))
        self.pipeline_config['instance_links'].update(links)
        jsondata = get_template(
            template_file='infrastructure/app_data.json.j2', appinfo=self.appinfo, pipeline_config=self.pipeline_config)
        self.log.debug('jsondata is %s', pformat(jsondata))
        return jsondata

    def retrieve_instance_links(self):
        """Appends on existing instance links

        Returns:
            instance_links: A dictionary containing all the instance links in LINKS and not in pipeline_config
        """
        instance_links = {}
        self.log.debug("LINKS IS %s", LINKS)
        for key, value in LINKS.items():
            if value not in self.pipeline_config['instance_links'].values():
                instance_links[key] = value
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
        url = '{gate}/credentials'.format(gate=API_URL)
        response = requests.get(url, verify=GATE_CA_BUNDLE, cert=GATE_CLIENT_CERT)
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
