#   Foremast - Pipeline Tooling
#
#   Copyright 2016 Gogo, LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""Module for creating an application in spinnaker.

Looks to see if the application exists, and if not creates the application.
"""
import logging
from pprint import pformat

import requests

from ..consts import API_URL, GATE_CA_BUNDLE, GATE_CLIENT_CERT
from ..exceptions import ForemastError
from ..utils import check_task, get_template, post_task


class SpinnakerApp:
    """Class to manage and create Spinnaker applications

    Args:
        app (str): Application name.
        email (str): Email associated with application.
        project (str): Git namespace or project group
        repo (str): Repository name

    Attributes:
        appinfo (dict): A dictionary containing the provided arguments
        appname (str): The name of the application.
    """

    def __init__(self, app=None, email=None, project=None, repo=None):
        self.log = logging.getLogger(__name__)

        self.appinfo = {'app': app,
                        'email': email,
                        'project': project,
                        'repo': repo}
        self.appname = app

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
        response = requests.get(url,
                                verify=GATE_CA_BUNDLE,
                                cert=GATE_CLIENT_CERT)
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

    def create_app(self):
        """Send a POST to spinnaker to create a new application with class variables.

        Raises:
            AssertionError: Application creation failed.
        """
        self.appinfo['accounts'] = self.get_accounts()
        self.log.debug('App info:\n%s', pformat(self.appinfo))

        jsondata = get_template(template_file='infrastructure/app_data.json.j2',
                                appinfo=self.appinfo)

        taskid = post_task(jsondata)
        check_task(taskid)

        self.log.info("Successfully created %s application", self.appname)
        return
