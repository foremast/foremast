"""Create Pipelines for Spinnaker."""
import json
import logging
import os
from pprint import pformat

import requests

from ..consts import API_URL
from ..exceptions import SpinnakerPipelineCreationFailed
from ..utils import (generate_encoded_user_data, get_app_details, get_subnets,
                     get_template)
from .clean_pipelines import clean_pipelines


class SpinnakerPipeline:
    """Manipulate Spinnaker Pipelines.

    Args:
        app_name: Str of application name.
    """

    def __init__(self, app_info):
        self.log = logging.getLogger(__name__)

        self.header = {'content-type': 'application/json'}
        self.here = os.path.dirname(os.path.realpath(__file__))

        self.app_info = app_info
        self.generated = get_app_details.get_details(app=self.app_info['app'])
        self.app_name = self.generated.app_name()
        self.group_name = self.generated.project

        self.settings = self.get_settings(self.app_info['properties'])

    @staticmethod
    def get_settings(property_file=''):
        """Get the specified Application configurations.

        Args:
            property_file (str): Name of JSON property file, e.g.
                raw.properties.json.
        """
        with open(property_file, 'rt') as data_file:
            data = json.load(data_file)
        return data

    def post_pipeline(self, pipeline_json):
        """Send Pipeline JSON to Spinnaker."""
        url = "{0}/pipelines".format(API_URL)
        self.log.debug('Pipeline JSON:\n%s', pipeline_json)

        pipeline_response = requests.post(url,
                                          data=pipeline_json,
                                          headers=self.header)

        self.log.debug('Pipeline creation response:\n%s',
                       pipeline_response.text)

        if not pipeline_response.ok:
            raise SpinnakerPipelineCreationFailed(
                'Failed to create pipeline for {0}: {1}'.format(
                    self.app_name, pipeline_response.json()))

        self.log.info('Successfully created "%s" pipeline',
                      json.loads(pipeline_json)['name'])

    def create_pipeline(self):
        """Send a POST to spinnaker to create a new security group."""
        clean_pipelines(app=self.app_name, settings=self.settings)

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
        stages = json.loads(pipeline)['stages']
        for stage in more_stages:
            stages += json.loads(stage)
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

        pipeline = json.loads(pipeline)
        pipeline['stages'] = stages

        return json.dumps(pipeline)

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
            template_name = 'pipeline-templates/pipeline_wrapper.json'
        elif env.startswith('prod'):
            template_name = 'pipeline-templates/pipeline_{}.json'.format(env)
        else:
            template_name = 'pipeline-templates/pipeline_stages.json'

        self.log.debug('%s info:\n%s', env, pformat(self.app_info[env]))

        region_subnets = get_subnets(env=env, region=region)

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

        pipeline_json = get_template(template_file=template_name, data=data)
        return pipeline_json
