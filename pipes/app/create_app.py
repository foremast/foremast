#!/usr/bin/env python

# A script for creating an application in spinnaker.
# Simply looks to see if the application already exists, if not, creates

import argparse
import configparser
import json
import logging
import os
import sys
import gogoutils

from jinja2 import Environment, FileSystemLoader
import requests


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
        jsondata = self.setup_appdata()
        r = requests.post(url, data=json.dumps(jsondata), headers=self.header)

        if not r.ok:
            logging.error("Failed to create app: {}".format(r.text))
            sys.exit(1)

        logging.info("Successfully created {} application".format(self.appname))
        return

if __name__ == "__main__":
    # Setup parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", help="The application name to create",
                        required=True)
    parser.add_argument("--email", help="Email address to associate with application",
                        default="PS-DevOpsTooling@example.com")
    parser.add_argument("--project", help="The project to associate with application",
                        default="None")
    parser.add_argument("--repo", help="The repo to associate with application",
                        default="None")
    parser.add_argument("--git", help="Git URI", default=None)
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

    if args.git:
        generated = gogoutils.Generator(*gogoutils.Parser(args.git).parse_url())
        project = generated.project
        repo = generated.repo
    else:
        project = args.project
        repo = args.repo

    # Dictionary containing application info. This is passed to the class for processing
    appinfo = {
        "app": args.app,
        "email": args.email,
        "project": project,
        "repo": repo
    }

    spinnakerapps = SpinnakerApp()
    spinnakerapps.create_app(appinfo=appinfo)
