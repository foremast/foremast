"""Create Security Groups for Spinnaker Pipelines."""
import argparse
import configparser
import json
import logging
import os
import sys

from jinja2 import Environment, FileSystemLoader
import requests

class SpinnakerSecurityGroup:
    def __init__(self):
        self.here = os.path.dirname(os.path.realpath(__file__))

        self.config = self.get_configs()

        self.gate_url = self.config['spinnaker']['gate_url']

        self.header = {'content-type': 'application/json'}

    def get_configs(self):
        """Get main configuration.

        Returns:
            configparser.ConfigParser object with configuration loaded.
        """
        config = configparser.ConfigParser()
        configpath = "{}/../../configs/spinnaker.conf".format(self.here)
        config.read(configpath)
        return config

    def get_template(self, template_name, **kwargs):
        """Get Jinja2 Template _template_name_.

        Args:
            template_name: Str of template name to retrieve.
            kwargs: Keyword arguments to use for template rendering.

        Returns:
            Dict of rendered JSON to send to Spinnaker.
        """
        templatedir = "{}/../../templates".format(self.here)
        jinja_env = Environment(loader=FileSystemLoader(templatedir))
        template = jinja_env.get_template(template_name)
        rendered_json = json.loads(template.render(**kwargs))
        return rendered_json

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

    '''Sends a POST to spinnaker to create a new application'''
    def create_security_group(self, appinfo=None):
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
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

    #Dictionary containing application info. This is passed to the class for processing
    appinfo = { "name": args.name,
                "email": args.email,
                "project": args.project,
                "repo": args.repo }

    spinnakerapps = SpinnakerSecurityGroup()
    spinnakerapps.create_security_group(appinfo=appinfo)
