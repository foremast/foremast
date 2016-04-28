"""Create Pipelines for Spinnaker."""
import configparser
import json
import logging
import os
from pprint import pformat

import murl
import requests
from jinja2 import Environment, FileSystemLoader
from tryagain import retries

from ..utils import (check_managed_pipeline, generate_encoded_user_data,
                    get_subnets)


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
        self.app_name = ''
        self.group_name = ''
        self.app_exists()

        self.settings = self.get_settings()

    def get_settings(self):
        """Get the specified Application configurations."""
        with open(self.app_info['properties']) as data_file:
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
        templatedir = "{}/../../templates/pipeline-templates".format(self.here)
        jinja_env = Environment(loader=FileSystemLoader(templatedir))
        template = jinja_env.get_template(template_name)

        rendered_template = template.render(**template_dict)
        self.log.debug('Rendered template:\n%s', rendered_template)
        rendered_json_dict = json.loads(rendered_template)
        self.log.debug('Rendered JSON dict: %s', rendered_json_dict)
        return rendered_json_dict

    def clean_pipelines(self):
        """Delete Pipelines for regions not defined in application.json files.

        For Pipelines named **app_name [region]**, _region_ will need to appear
        in at least one application.json file. All other names are assumed
        unamanaged.

        Returns:
            True: Upon successful completion.
        """
        url = murl.Url(self.gate_url)
        pipelines = self.get_all_pipelines(app=self.app_info['app']).json()

        envs = self.settings['pipeline']['env']
        self.log.debug('Find Regions in: %s', envs)

        regions = set()
        for env in envs:
            regions.update(self.settings[env]['regions'])
        self.log.debug('Regions defined: %s', regions)

        for pipeline in pipelines:
            pipeline_name = pipeline['name']

            try:
                region = check_managed_pipeline(name=pipeline_name,
                                                app_name=self.app_name)
            except ValueError:
                self.log.info('"%s" is not managed.', pipeline_name)
                continue

            self.log.debug('Check "%s" in defined Regions.', region)

            if region not in regions:
                self.log.warning('Deleting Pipeline: %s', pipeline_name)

                url.path = 'pipelines/{app}/{pipeline}'.format(
                    app=self.app_info['app'],
                    pipeline=pipeline_name)
                response = requests.delete(url.url)

                self.log.debug('Deleted "%s" Pipeline response:\n%s',
                               pipeline_name, response.text)

        return True

    def post_pipeline(self, pipeline_json):
        """Send Pipeline JSON to Spinnaker."""
        url = "{0}/pipelines".format(self.gate_url)
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

        logging.info('Successfully created %s pipeline', pipeline_json['name'])

    def create_pipeline(self):
        """Send a POST to spinnaker to create a new security group."""
        self.clean_pipelines()
        previous_env = None

        self.log.info('Creating wrapper template')
        self.log.debug('Envs: %s', self.settings['pipeline']['env'])

        # sets up dict for managing region specific pipelines
        # generates pipeline wrapper per region
        regiondict = {}
        for env in self.settings['pipeline']['env']:
            for region in self.settings[env]['regions']:
                pipeline_json = self.construct_pipeline_block(
                    env=env,
                    previous_env=None,
                    next_env=None,
                    region=region,
                    wrapper=True)
                regiondict[region] = [pipeline_json]

        self.log.debug('Region dict:\n%s', regiondict)

        for index, env in enumerate(self.settings['pipeline']['env']):
            # Assume order of environments is correct
            try:
                next_env = self.settings['pipeline']['env'][index + 1]
            except IndexError:
                next_env = None

            for region in self.settings[env]['regions']:
                if env in self.settings['pipeline']:
                    # The custom provided pipeline
                    self.log.info('Found overriding Pipeline JSON for %s.',
                                  env)
                    pipeline_json = self.settings['pipeline'].get(env, None)
                    self.post_pipeline(pipeline_json)
                else:
                    self.log.info('Using predefined template for %s.', env)
                    pipeline_json = self.construct_pipeline_block(
                        env=env,
                        previous_env=previous_env,
                        region=region,
                        next_env=next_env)
                    regiondict[region].append(pipeline_json)

            previous_env = env

        # builds pipeline for each region
        for key in regiondict.keys():
            newpipeline = self.combine_pipelines(regiondict[key])
            self.post_pipeline(newpipeline)

        return True

    def combine_pipelines(self, pipeline_list):
        """Combine _pipeline_list_ into single pipeline for Spinnaker.

        +---------+------------------------+------------+
        | refId   | stage                  | requires   |
        +=========+========================+============+
        | 0       | config                 |            |
        +---------+------------------------+------------+
        | 1       | bake                   |            |
        +---------+------------------------+------------+
        | 100     | git tagger packaging   | 1          |
        +---------+------------------------+------------+
        | 2       | deploy dev             | 1          |
        +---------+------------------------+------------+
        | 3       | QE dev                 | 2          |
        +---------+------------------------+------------+
        | 200     | git tagger dev         | 2          |
        +---------+------------------------+------------+
        | 4       | judgement              | 3          |
        +---------+------------------------+------------+
        | 5       | deploy stage           | 4          |
        +---------+------------------------+------------+
        | 6       | QE stage               | 5          |
        +---------+------------------------+------------+
        | 500     | git tagger stage       | 5          |
        +---------+------------------------+------------+

        Args:
            pipeline_list (list): List of pipelines to combine..

        Returns:
            dict: dictionary of one big pipeline.
        """
        self.log.debug('Pipeline list: %s', pipeline_list)

        pipeline, *more_stages = pipeline_list
        stages = pipeline['stages']
        for stage in more_stages:
            stages += stage
        self.log.debug('Combined Stages:\n%s', pformat(stages))

        main_index = 1
        for stage in stages:
            if stage['name'].startswith('Git Tag'):
                stage['requisiteStageRefIds'] = [str(main_index)]
                stage['refId'] = str(main_index * 100)
            elif stage['name'].startswith('Log Deploy'):
                stage['requisiteStageRefIds'] = [str(main_index)]
                stage['refId'] = str(main_index * 101)
            elif stage['type'] == 'bake':
                stage['requisiteStageRefIds'] = []
                stage['refId'] = str(main_index)
            else:
                stage['requisiteStageRefIds'] = [str(main_index)]
                main_index += 1
                stage['refId'] = str(main_index)

            self.log.debug('step=%(name)s\trefId=%(refId)s\t'
                           'requisiteStageRefIds=%(requisiteStageRefIds)s',
                           stage)

        self.log.debug('Deleting last Manual Judgement, Stage not needed.')
        del stages[-1]

        return pipeline

    def construct_pipeline_block(self,
                                 env='',
                                 previous_env=None,
                                 next_env=None,
                                 region='us-east-1',
                                 wrapper=False):
        """Create the Pipeline JSON from template.

        Args:
            env (str): Deploy environment name, e.g. dev, stage, prod.
            previous_env (str): The previous deploy environment to use as
                Trigger.
            next_env (str): Name of next deployment environment.
            region (str): AWS Region to deploy to.

        Returns:
            dict: Pipeline JSON template rendered with configurations.
        """
        self.app_info[env] = self.settings[env]
        self.log.info('Create Pipeline for %s in %s.', env, region)

        self.log.debug('App info:\n%s', self.app_info)

        if wrapper:
            # use pipeline template
            template_name = 'pipeline_wrapper.json'
        elif (env == 'prods'):
            template_name = 'pipeline_prods.json'
        elif (env == 'prodp'):
            template_name = 'pipeline_prodp.json'
        else:
            template_name = 'pipeline_stages.json'

        raw_subnets = get_subnets()
        print(raw_subnets)
        self.log.debug('%s info:\n%s', env, pformat(self.app_info[env]))

        region_subnets = {region: raw_subnets[env][region]}

        self.log.debug('Region and subnets in use:\n%s', region_subnets)

        # Use different variable to keep template simple
        data = self.app_info[env]
        data['app'].update({
            'appname': self.app_info['app'],
            'environment': env,
            'triggerjob': self.app_info['triggerjob'],
            'regions': json.dumps(list(region_subnets.keys())),
            'region': region,
            'az_dict': json.dumps(region_subnets),
            'previous_env': previous_env,
            'next_env': next_env,
            'encoded_user_data': generate_encoded_user_data(
                env=env,
                region=region,
                app_name=self.app_name,
                group_name=self.group_name),
        })

        pipeline_json = self.get_template(template_name=template_name,
                                          template_dict=data, )
        return pipeline_json

    def app_exists(self):
        """Check to see if application already exists.

        Sets self.app_name and self.group_name based on Spinnaker Application
        attributes.

        Returns:
            bool: True when Spinnaker Application exists.

        Raises:
            SpinnakerAppNotFound: Could not find Spinnaker Application.
        """
        app_name = self.app_info['app']

        url = murl.Url(self.gate_url)
        url.path = 'applications/{app}'.format(app=app_name)
        app_response = requests.get(url.url, headers=self.header)

        if app_response.ok:
            app_dict = app_response.json()
            self.app_name = app_dict['attributes']['name']
            self.group_name = app_dict['attributes']['repoProjectKey']
            return True
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
                self.log.debug('ID of %(name)s: %(id)s', pipeline)

                if pipeline['name'] == name:
                    return_id = pipeline['id']
                    self.log.info('Pipeline %s found, ID: %s', name, return_id)
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
