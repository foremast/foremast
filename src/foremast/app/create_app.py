"""A script for creating an application in spinnaker.

Simply looks to see if the application already exists, if not, creates.
"""
import configparser
import json
import logging
import os
import sys

import requests
from jinja2 import Environment, FileSystemLoader


class SpinnakerApp:
    def __init__(self):
        config = configparser.ConfigParser()
        self.here = os.path.dirname(os.path.realpath(__file__))
        configpath = "{}/../../configs/spinnaker.conf".format(self.here)
        config.read(configpath)
        self.gate_url = config['spinnaker']['gate_url']
        self.header = {'content-type': 'application/json'}

    def get_apps(self):
        '''Gets all applications from spinnaker'''
        url = self.gate_url + "/applications"
        r = requests.get(url)
        if r.status_code == 200:
            self.apps = r.json()
        else:
            logging.error(r.text)
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
            logging.error(r.text)
            sys.exit(1)

    def app_exists(self):
        '''Checks to see if application already exists'''
        self.get_apps()
        for app in self.apps:
            if app['name'].lower() == self.appname.lower():
                logging.info('{} app already exists'.format(self.appname))
                return True
        logging.info('{} does not exist...creating'.format(self.appname))
        return False

    def setup_appdata(self):
        '''Uses jinja2 to setup POST data for application creation'''
        templatedir = "{}/../../templates".format(self.here)
        jinjaenv = Environment(loader=FileSystemLoader(templatedir))
        template = jinjaenv.get_template("app_data_template.json")
        rendered_json = json.loads(template.render(appinfo=self.appinfo))
        print(rendered_json)
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
            logging.error("Failed to create app: {}".format(r.text))
            sys.exit(1)

        logging.info("Successfully created {} application".format(self.appname))
        return
