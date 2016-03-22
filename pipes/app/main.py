#!/usr/bin/env python

#A script for creating an application in spinnaker.
#Simply looks to see if the application already exists, if not, creates

import json
import logging
import os
import sys
import argparse

from jinja2 import Environment, FileSystemLoader
import requests

class SpinnakerApp:
    def __init__(self):
        self.gate_url = "http://spinnaker.build.example.com:8084"
        self.header = {'content-type': 'application/json'}

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
            
    '''Uses jinja2 to setup POST data for application creation'''
    def setup_appdata(self):
        curdir = os.path.dirname(os.path.realpath(__file__))
        templatedir = "{}/../../templates".format(curdir)
        jinjaenv = Environment(loader=FileSystemLoader(templatedir))
        template = jinjaenv.get_template("app_data_template.json")
        rendered_json = json.loads(template.render(appinfo=self.appinfo))
        return rendered_json

    '''Sends a POST to spinnaker to create a new application'''
    def create_app(self, appinfo=None):
        #setup class variables for processing
        self.appinfo = appinfo
        if appinfo:
            self.appname = appinfo['name']

        if not (self.app_exists()):
            url = "{}/applications/{}/tasks".format(self.gate_url, self.appname)
            jsondata = self.setup_appdata()
            r = requests.post(url, data=json.dumps(jsondata), headers=self.header)
            
            if r.status_code != 200:
                logging.error("Failed to create app: {}".format(r.text))
                sys.exit(1)

            logging.info("Successfully created {} application".format(self.appname))
            return

if __name__ == "__main__":
    #Setup parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", help="The application name to create",
                        required=True)
    parser.add_argument("--email", help="Email address to associate with application",
                        default="PS-DevOpsTooling@example.com")
    parser.add_argument("--project", help="The project to associaste with application",
                        default="None")
    parser.add_argument("--repo", help="The repo to associaste with application",
                        default="None")
    parser.add_argument("--description", help="The application description",
                        default="None")
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

    #Dictionary containing application info. This is passed to the class for processing
    appinfo = { "name": args.name, 
                "email": args.email,
                "project": args.project, 
                "repo": args.repo, 
                "description": args.description } 

    spinnakerapps = SpinnakerApp()
    spinnakerapps.create_app(appinfo=appinfo)

