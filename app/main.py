import logging
import sys

import requests

class SpinnakerApp:
    def __init__(self):
        logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
        self.gate_url = "http://spinnaker.build.example.com:8084"

    def get_apps(self):
        url = self.gate_url + "/applications"
        r = requests.get(url)
        if r.status_code == 200:
            self.apps = r.json()
        else:
            logging.error(r.text)
            sys.exit(1)

    def app_exists(self, appname=None):
        for app in self.apps:
            if app['name'].lower() == appname.lower():
                logging.info('{} app already exists'.format(appname))
                return True
        logging.info('{} does not exist...creating'.format(appname))
        return False

    

if __name__ == "__main__":
    spinnakerapps = SpinnakerApp()
    spinnakerapps.get_apps()
    exists = spinnakerapps.app_exists(appname='test1234')

