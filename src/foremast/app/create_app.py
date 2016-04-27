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

    def get_apps(self):
        '''Gets all applications from spinnaker'''
        url = self.gate_url + "/applications"
        r = requests.get(url)
        if r.status_code == 200:
            self.apps = r.json()
        else:
            self.log.error(r.text)
            sys.exit(1)

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

    def app_exists(self):
        '''Checks to see if application already exists'''
        self.get_apps()
        for app in self.apps:
            if app['name'].lower() == self.appname.lower():
                self.log.info('%s app already exists', self.appname)
                return True
        self.log.info('%s does not exist...creating', self.appname)
        return False

    def setup_appdata(self):
        '''Uses jinja2 to setup POST data for application creation'''
        rendered_json = get_template(template_file='app_data_template.json',
                                     appinfo=self.appinfo)
        self.log.debug(rendered_json)
        return rendered_json

    def create_app(self, appinfo=None):
        '''Sends a POST to spinnaker to create a new application'''
        # setup class variables for processing
        self.appinfo = appinfo
        if appinfo:
            self.appname = appinfo['app']

        url = "{}/applications/{}/tasks".format(self.gate_url, self.appname)
        self.appinfo['accounts'] = self.get_accounts()
        jsondata = self.setup_appdata()
        r = requests.post(url, data=json.dumps(jsondata), headers=self.header)

        if not r.ok:
            self.log.error("Failed to create app: %s", r.text)
            sys.exit(1)

        self.log.info("Successfully created %s application", self.appname)
        return
