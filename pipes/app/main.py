#!/usr/bin/env python

#A script for creating an application in spinnaker.
#Simply looks to see if the application already exists, if not, creates

import json
import logging
import os
import sys

from jinja2 import Environment, FileSystemLoader
import requests

class SpinnakerApp:
    def __init__(self, appinfo=None):
        logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
        self.gate_url = "http://spinnaker.build.example.com:8084"
        self.header = {'content-type': 'application/json'}
        self.appinfo = appinfo
        if appinfo:
            self.appname = appinfo['name']

    '''Gets all applications from spinnaker'''
    def get_apps(self):
        url = self.gate_url + "/applications"
        r = requests.get(url)
        if r.status_code == 200:
            self.apps = r.json()
        else:
            logging.error(r.text)
            sys.exit(1)

    '''Checks to see if application already exists'''
    def app_exists(self):
        self.get_apps()
        for app in self.apps:
            if app['name'].lower() == self.appname.lower():
                logging.info('{} app already exists'.format(self.appname))
                return True
        logging.info('{} does not exist...creating'.format(self.appname))
        return False
            
    '''Uses jinja2 to setup POST data for appliucation creation'''
    def setup_appdata(self):
        curdir = os.path.dirname(os.path.realpath(__file__))
        templatedir = "{}/../../templates".format(curdir)
        jinjaenv = Environment(loader=FileSystemLoader(templatedir))
        template = jinjaenv.get_template("app_data_template.json")
        print(template.render(appinfo=appinfo))


    '''Sends a POST to spinnaker to create a new application'''
    def create_app(self):
        if not (self.app_exists()):
            url = "{}/applications/{}/tasks".format(self.gate_url, self.appname)
            self.setup_appdata()
            #data = json.dumps(self.app_dict)
            #r = requests.post(url, data=data, headers=self.header)
            #print(r.text)
            return

if __name__ == "__main__":
    appinfo = { "name": "DougTest", "email": "dcampbell@example.com",
            "project": "DougTest", "repo": "DougRepo", "Description": "this is a test"}
    spinnakerapps = SpinnakerApp(appinfo=appinfo)
    spinnakerapps.create_app()

