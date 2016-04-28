"""A script for creating an application in spinnaker.

Simply looks to see if the application already exists, if not, creates.
"""
import logging

import requests

from ..utils import get_configs, get_template


class SpinnakerApp:
    """Spinnaker Application creation."""

    def __init__(self, appinfo=None):
        self.log = logging.getLogger(__name__)

        self.appinfo = appinfo
        self.appname = self.appinfo['app']

        config = get_configs('spinnaker.conf')
        self.gate_url = config['spinnaker']['gate_url']
        self.header = {'content-type': 'application/json'}

    def get_accounts(self, provider='aws'):
        """Get Accounts added to Spinnaker.

        Args:
            provider (str): What provider to find accounts for.

        Returns:
            list: Dicts of Spinnaker credentials matching _provider_.

        Raises:
            AssertionError: Failure getting accounts from Spinnaker.
        """
        url = '{gate}/credentials'.format(gate=self.gate_url)
        r = requests.get(url)

        assert r.ok, 'Failed to get accounts: {0}'.format(r.text)

        all_accounts = r.json()
        filtered_accounts = []
        for account in all_accounts:
            if account['type'] == provider:
                filtered_accounts.append(account)

        return filtered_accounts

    def create_app(self):
        """Send a POST to spinnaker to create a new application.

        Raises:
            AssertionError: Application creation failed.
        """
        self.appinfo['accounts'] = self.get_accounts()

        jsondata = get_template(template_file='app_data_template.json',
                                appinfo=self.appinfo)

        url = "{}/applications/{}/tasks".format(self.gate_url, self.appname)
        r = requests.post(url, data=jsondata, headers=self.header)

        assert r.ok, 'Failed to create "{0}": {1}'.format(self.appname, r.text)

        self.log.info("Successfully created %s application", self.appname)
        return
