import logging
import sys
import json

from jinja2 import Environment, PackageLoader
import requests

class SpinnakerApp:
    def __init__(self):
        logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
        self.gate_url = "http://spinnaker.build.example.com:8084"
        self.app_dict = app_dict
        self.header = {'content-type': 'application/json'}

    def get_apps(self):
        url = self.gate_url + "/applications"
        r = requests.get(url)
        if r.status_code == 200:
            self.apps = r.json()
        else:
            logging.error(r.text)
            sys.exit(1)

    def app_exists(self, appname=None):
        self.get_apps()
        for app in self.apps:
            if app['name'].lower() == appname.lower():
                logging.info('{} app already exists'.format(appname))
                return True
        logging.info('{} does not exist...creating'.format(appname))
        return False

    def setup_data(self,appname=None):
        for idx, item in enumerate(self.app_dict['job']):
            self.app_dict['job'][idx]['application']['name'] == appname

        self.app_dict['application'] == appname
        self.app_dict['description'] == 'Create application: {}'.format(appname)
            
    def setup_json(self):


    def create_app(self, appname=None):
        url = "{}/applications/{}/tasks".format(self.gate_url, appname)
        self.setup_data(appname=appname)
        data = json.dumps(self.app_dict)
        print(data)
        #r = requests.post(url, data=data, headers=self.header)
        #print(r.text)
        return

if __name__ == "__main__":
    appinfo = { "name": "DougTest", "email": "dcampbell@example.com",
                "project": "DougTest", "repo': '
    spinnakerapps = SpinnakerApp()
    exists = spinnakerapps.app_exists(appname='test1234')
    if not exists:
        spinnakerapps.create_app(appname="DougTest")

