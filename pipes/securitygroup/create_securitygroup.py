"""Create Security Groups for Spinnaker Pipelines."""
import argparse
import configparser
import json
import logging
import os
import sys

from jinja2 import Environment, FileSystemLoader
import requests


class SpinnakerAppNotFound(Exception):
    pass


class SpinnakerApplicationListError(Exception):
    pass


class SpinnakerSecurityGroupCreationFailed(Exception):
    pass


class SpinnakerSecurityGroup:
    """Manipulate Spinnaker Security Groups.

    Args:
        app_name: Str of application name add Security Group to.
    """

    def __init__(self, app_info):
        self.log = logging.getLogger(__name__)

        self.app_name = self.app_exists(app_name=app_info['name'])
        self.app_info = app_info

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

    def get_template(self, template_name='', template_dict=None):
        """Get Jinja2 Template _template_name_.

        Args:
            template_name: Str of template name to retrieve.
            template_dict: Dict to use for template rendering.

        Returns:
            Dict of rendered JSON to send to Spinnaker.
        """
        templatedir = "{}/../../templates".format(self.here)
        jinja_env = Environment(loader=FileSystemLoader(templatedir))
        template = jinja_env.get_template(template_name)

        rendered_json = json.loads(template.render(**template_dict))
        return rendered_json

    def get_apps(self):
        """Gets all applications from spinnaker."""
        url = '{0}/applications'.format(self.gate_url)
        r = requests.get(url)
        if r.ok:
            return r.json()
        else:
            logging.error(r.text)
            raise SpinnakerApplicationListError(r.text)

    def app_exists(self, app_name):
        """Checks to see if application already exists.

        Args:
            app_name: Str of application name to check.

        Returns:
            Str of application name

        Raises:
            SpinnakerAppNotFound
        """

        apps = self.get_apps()
        app_name = app_name.lower()
        for app in apps:
            if app['name'].lower() == app_name:
                logging.info('Application %s found!', app_name))
                return app_name

        logging.info('Application %s does not exist ... exiting', app_name))
        raise SpinnakerAppNotFound('Application "{0}" not found.'.format(app_name))

    def create_security_group(self):
        """Sends a POST to spinnaker to create a new security group."""

        app_name = self.app_name

        url = "{0}/applications/{1}/tasks".format(self.gate_url,
                                                self.app_name)

        secgroup_json = self.get_template(
            template_name='securitygroup_template.json',
            template_dict=self.app_info,
        )

        r = requests.post(url,
                          data=json.dumps(secgroup_json),
                          headers=self.header)

        if not r.ok:
            logging.error('Failed to create app: %s', r.text))
            raise SpinnakerSecurityGroupCreationFailed(r.text)

        logging.info('Successfully created %s security group', self.app_name)
        return


def main():
    """Run newer stuffs."""
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument("--name",
                        help="The application name to create",
                        required=True)
    parser.add_argument("--region",
                        help="The application name to create",
                        required=True)
    parser.add_argument("--vpc",
                        help="The application name to create",
                        required=True)
    parser.add_argument("--environment",
                        help="The application name to create",
                        required=True)
    parser.add_argument("--subnet",
                        help="The application name to create",
                        required=True)
    args = parser.parse_args()

    log.debug('Parsed arguments: %s', args)

    #Dictionary containing application info. This is passed to the class for processing
    appinfo = {'name': args.name,
               'vpc': args.vpc,
               'region': args.region,
               'environment': args.environment,
               'subnet': args.subnet, }

    spinnakerapps = SpinnakerSecurityGroup(app_info=appinfo)
    sg_json = spinnakerapps.get_template(
        template_name='securitygroup_template.json',
        template_dict=appinfo)
    print('SG JSON:\n', sg_json)
    # spinnakerapps.create_security_group(appinfo=appinfo)


if __name__ == "__main__":
    main()
