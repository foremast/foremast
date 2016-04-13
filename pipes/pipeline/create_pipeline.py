"""Create Pipelines for Spinnaker"""
import argparse
import configparser
import json
import logging
import os

import murl
import requests
from jinja2 import Environment, FileSystemLoader
from tryagain import retries
from utils import get_subnets


class SpinnakerAppNotFound(Exception):
    """Missing Spinnaker Application."""
    pass


class SpinnakerApplicationListError(Exception):
    """Issue with getting list of all Spinnaker Applications."""
    pass


class SpinnakerPipelineCreationFailed(Exception):
    """Could not create Spinnaker Pipeline."""
    pass


class SpinnakerPipeline:
    """Manipulate Spinnaker Pipelines.

    Args:
        app_name: Str of application name.
    """

    def __init__(self, app_info):
        self.log = logging.getLogger(__name__)

        self.header = {'content-type': 'application/json'}
        self.here = os.path.dirname(os.path.realpath(__file__))

        self.config = self.get_configs()
        self.gate_url = self.config['spinnaker']['gate_url']

        self.app_info = app_info
        self.app_name = self.app_exists()

        self.settings = self.get_settings()

    @staticmethod
    def get_settings():
        """Get the specified Application configurations."""
        with open('../raw.properties.json') as data_file:
            data = json.load(data_file)
        return data

    def get_configs(self):
        """Get main configuration.

        Returns:
            configparser.ConfigParser object with configuration loaded.
        """
        config = configparser.ConfigParser()
        configpath = "{}/../../configs/spinnaker.conf".format(self.here)
        config.read(configpath)

        self.log.debug('Configuration sections found: %s', config.sections())
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
        self.log.debug('Rendered template: %s', rendered_json)
        return rendered_json

    def clean_pipelines(self):
        """Delete Pipelines not defined in pipeline.json.

        Returns:
            True: Existing Pipelines match defined Pipelines.
        """
        defined_envs = self.settings['pipeline']['env']
        current_envs = []
        all_pipelines = self.get_all_pipelines('{app}'.format(**self.app_info))

        for pipeline in all_pipelines.json():
            if pipeline['name'].endswith('-Pipeline'):
                app, env, _ = pipeline['name'].split('-')
                current_envs.append(env)

        self.log.debug('Pipelines found - User (%s), Spinnaker (%s)',
                       defined_envs, current_envs)

        if sorted(defined_envs) == sorted(current_envs):
            return True
        else:
            removed_pipelines = list(set(current_envs) - set(defined_envs))

            for pipeline in removed_pipelines:
                app = self.app_info['app']
                pipeline_name = '{app}-{env}-Pipeline'.format(app=app,
                                                              env=pipeline, )
                self.log.info('Deleted pipeline: %s', pipeline_name)
                url = murl.Url(self.gate_url)
                url.path = 'pipelines/{app}/{pipeline_name}'.format(
                    app=app,
                    pipeline_name=pipeline_name, )
                response = requests.delete(url.url)
                self.log.debug('Delete %s Pipeline response:\n%s', pipeline,
                               response.text)

    def create_pipeline(self):
        """Sends a POST to spinnaker to create a new security group."""
        url = "{0}/pipelines".format(self.gate_url)

        self.clean_pipelines()
        previous_env = None
        self.log.debug('Envs: %s', self.settings['pipeline']['env'])
        for env in self.settings['pipeline']['env']:
            # Assume order of environments is correct
            if env in self.settings['pipeline']:
                self.log.info('Found overriding Pipeline JSON for %s.', env)
                pipeline_json = self.settings['pipeline'].get(env, None)
            else:
                self.log.info('Using predefined template for %s.', env)
                pipeline_json = self.construct_pipline(
                    env=env,
                    previous_env=previous_env)

            self.log.debug('Pipeline JSON:\n%s', pipeline_json)

            pipeline_response = requests.post(url,
                                              data=json.dumps(pipeline_json),
                                              headers=self.header)

            self.log.debug('Pipeline creation response:\n%s',
                           pipeline_response.text)

            if not pipeline_response.ok:
                logging.error('Failed to create pipeline: %s',
                              pipeline_response.text)
                raise SpinnakerPipelineCreationFailed(pipeline_response.json())

            logging.info('Successfully created %s pipeline', self.app_name)

            previous_env = env

        return True

    def construct_pipline(self, env='', previous_env=None):
        """Create the Pipeline JSON from template.

        Args:
            env (str): Deploy environment name, e.g. dev, stage, prod.
            previous_env (str): The previous deploy environment to use as
                Trigger.

        Returns:
            str: Pipeline JSON template rendered with configurations.
        """
        self.app_info[env] = self.settings[env]

        self.log.debug('App info:\n%s', self.app_info)

        if previous_env:
            # use pipeline template
            template_name = 'pipeline_pipelinetrigger_template.json.j2'
            pipeline_id = self.get_pipe_id('{0}-{1}-Pipeline'.format(
                self.app_info['app'], previous_env))
            self.app_info[env].update({'pipeline_id': pipeline_id})
        else:
            # use template that uses jenkins
            template_name = 'pipeline_template.json'

        # Use different variable to keep template simple
        data = self.app_info[env]
        data['app']['appname'] = self.app_info['app']
        data['app']['environment'] = env
        data['app']['region'] = self.app_info['region']
        data['app']['subnets'] = get_subnets()[env][self.app_info['region']]
        pipeline_json = self.get_template(template_name=template_name,
                                          template_dict=data, )

        return pipeline_json

    def app_exists(self):
        """Checks to see if application already exists.

        Returns:
            Str of application name

        Raises:
            SpinnakerAppNotFound: Could not find Spinnaker Application.
        """
        app_name = self.app_info['app']

        url = murl.Url(self.gate_url)
        url.path = 'applications/{app}'.format(app=app_name)
        app_response = requests.get(url.url, headers=self.header)

        if app_response.ok:
            return app_name
        else:
            logging.info('Application %s does not exist ... exiting', app_name)
            raise SpinnakerAppNotFound('Application "{0}" not found.'.format(
                app_name))

    def get_all_pipelines(self, app=''):
        """Get a list of all the Pipelines in _app_.

        Args:
            app (str): Name of Spinnaker Application.

        Returns:
            requests.models.Response: Response from Gate containing Pipelines.
        """
        url = murl.Url(self.gate_url)
        url.path = 'applications/{app}/pipelineConfigs'.format(app=app)
        response = requests.get(url.url)
        return response

    def get_pipe_id(self, name=''):
        """Get the ID for Pipeline _name_.

        Args:
            name (str): Name of Pipeline to get ID for.

        Returns:
            str: ID of specified Pipeline.
            None: Pipeline or Spinnake Appliation not found.
        """
        return_id = None

        response = self.get_all_pipelines('{app}'.format(**self.app_info))

        if response.ok:
            pipe_configs = response.json()

            for pipeline in pipe_configs:
                self.log.info('ID of %(name)s: %(id)s', pipeline)

                if pipeline['name'] == name:
                    return_id = pipeline['id']
                    self.log.info('Pipeline found!')
                    break

        return return_id

    @retries(max_attempts=10, wait=10.0, exceptions=Exception)
    def check_task(self, taskid):
        """Check for the completion of _taskid_.

        Args:
            taskid (str): ID of Task to poll.

        Raises:
            Exception: Task has not completed yet.

        Returns:
            str: Task status of SUCCEEDED or TERMINAL.
        """
        try:
            taskurl = taskid.get('ref', '0000')
        except AttributeError:
            taskurl = taskid

        taskid = taskurl.split('/tasks/')[-1]

        self.log.info('Checking taskid %s', taskid)

        url = '{0}/applications/{1}/tasks/{2}'.format(self.gate_url,
                                                      self.app_name,
                                                      taskid, )

        task_response = requests.get(url, headers=self.header)

        self.log.debug(task_response.json())
        if not task_response.ok:
            raise Exception
        else:
            task_json = task_response.json()

            status = task_json['status']

            self.log.info('Current task status: %s', status)
            statuses = ('SUCCEEDED', 'TERMINAL')

            if status in statuses:
                return status
            else:
                raise Exception


def main():
    """Run newer stuffs."""
    logging.basicConfig(format='%(asctime)s %(message)s')
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument('-d',
                        '--debug',
                        action='store_const',
                        const=logging.DEBUG,
                        default=logging.INFO,
                        help='Set DEBUG output')
    parser.add_argument("--app",
                        help="The application name to create",
                        required=True)
    parser.add_argument("--region",
                        help="The region to create the security group",
                        required=True)
    parser.add_argument("--vpc",
                        help="The vpc to create the security group",
                        required=True)
    parser.add_argument("--triggerjob",
                        help="The job to monitor for pipeline triggering",
                        required=True)
    args = parser.parse_args()

    log.setLevel(args.debug)
    logging.getLogger(__package__).setLevel(args.debug)

    log.debug('Parsed arguments: %s', args)

    # Dictionary containing application info. This is passed to the class for
    # processing
    appinfo = {
        'app': args.app,
        'vpc': args.vpc,
        'region': args.region,
        'triggerjob': args.triggerjob
    }

    spinnakerapps = SpinnakerPipeline(app_info=appinfo)
    spinnakerapps.create_pipeline()


if __name__ == "__main__":
    main()
