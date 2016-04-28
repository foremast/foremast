"""A script for creating an application in spinnaker.

Simply looks to see if the application already exists, if not, creates.
"""
import json
import logging
import sys

import requests

from ..utils import get_configs, get_template


class SpinnakerApp:
    def __init__(self):
        config = get_configs('spinnaker.conf')
        self.gate_url = config['spinnaker']['gate_url']
        self.header = {'content-type': 'application/json'}
        self.log = logging.getLogger(__name__)

    def get_accounts(self, provider='aws'):
        url = '{gate}/credentials'.format(gate=self.gate_url)
        r = requests.get(url)
        if r.ok:
            all_accounts = r.json()
            filtered_accounts = []

            for account in all_accounts:
                if account['type'] == provider:
                    filtered_accounts.append(account)
            return filtered_accounts

        else:
            self.log.error(r.text)
            sys.exit(1)

    def create_app(self, appinfo=None):
        '''Sends a POST to spinnaker to create a new application'''
        # setup class variables for processing
        self.appinfo = appinfo
        if appinfo:
            self.appname = appinfo['app']

        url = "{}/applications/{}/tasks".format(self.gate_url, self.appname)
        self.appinfo['accounts'] = self.get_accounts()

        jsondata = get_template(template_file='app_data_template.json',
                                appinfo=self.appinfo)

        r = requests.post(url, data=jsondata, headers=self.header)

        if not r.ok:
            self.log.error("Failed to create app: %s", r.text)
            sys.exit(1)

        self.log.info("Successfully created %s application", self.appname)
        return
