"""Create Security Groups for Spinnaker Pipelines."""
import json
import logging
import os

import requests
from jinja2 import Environment, FileSystemLoader
from tryagain import retries

from ..consts import API_URL, HEADERS
from ..exceptions import (SpinnakerApplicationListError, SpinnakerAppNotFound,
                          SpinnakerSecurityGroupCreationFailed)
from ..utils import get_vpc_id


class SpinnakerSecurityGroup:
    """Manipulate Spinnaker Security Groups.

    Args:
        app_name: Str of application name add Security Group to.
    """

    def __init__(self, app_info):
        self.log = logging.getLogger(__name__)

        self.here = os.path.dirname(os.path.realpath(__file__))
        self.app_name = self.app_exists(app_name=app_info['app'])
        self.app_info = app_info

    def get_template(self, template_name='', template_dict=None):
        """Get Jinja2 Template _template_name_.

        Args:
            template_name: Str of template name to retrieve.
            template_dict: Dict to use for template rendering.

        Returns:
            Dict of rendered JSON to send to Spinnaker.
        """
        templatedir = '{0}/../templates/'.format(self.here)
        jinja_env = Environment(loader=FileSystemLoader(templatedir))
        template = jinja_env.get_template(template_name)

        rendered_json = json.loads(template.render(**template_dict))
        self.log.debug('Rendered template: %s', rendered_json)
        return rendered_json

    def get_apps(self):
        """Gets all applications from spinnaker."""
        url = '{0}/applications'.format(API_URL)
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
                logging.info('Application %s found!', app_name)
                return app_name

        logging.info('Application %s does not exist ... exiting', app_name)
        raise SpinnakerAppNotFound('Application "{0}" not found.'.format(
            app_name))

    @retries(max_attempts=10, wait=10.0, exceptions=Exception)
    def check_task(self, taskid):

        try:
            taskurl = taskid.get('ref', '0000')
        except AttributeError:
            taskurl = taskid

        taskid = taskurl.split('/tasks/')[-1]

        self.log.info('Checking taskid %s' % taskid)

        url = '{0}/applications/{1}/tasks/{2}'.format(API_URL,
                                                      self.app_name,
                                                      taskid, )

        r = requests.get(url, headers=HEADERS)

        self.log.debug(r.json())
        if not r.ok:
            raise Exception
        else:
            json = r.json()

            status = json['status']

            self.log.info('Current task status: %s', status)
            STATUSES = ('SUCCEEDED', 'TERMINAL')

            if status in STATUSES:
                return status
            else:
                raise Exception

    def create_security_group(self):
        """Sends a POST to spinnaker to create a new security group."""
        url = "{0}/applications/{1}/tasks".format(API_URL, self.app_name)

        app_data = {
            'vpc': get_vpc_id(self.app_info['env'], self.app_info['region']),
        }
        app_data.update(self.app_info)

        secgroup_json = self.get_template(
            template_name='securitygroup_template.json',
            template_dict=app_data, )

        r = requests.post(url, data=json.dumps(secgroup_json), headers=HEADERS)

        status = self.check_task(r.json())
        if status not in ('SUCCEEDED'):
            logging.error('Failed to create app: %s', r.text)
            raise SpinnakerSecurityGroupCreationFailed(r.text)

        logging.info('Successfully created %s security group', self.app_name)
        return True
