"""Create Pipelines for Spinnaker."""
import collections
import json
import logging
import os
from pprint import pformat

import requests

from ..consts import API_URL
from ..exceptions import SpinnakerPipelineCreationFailed, SpinnakerSubnetError
from ..utils import (generate_encoded_user_data, get_app_details, get_subnets,
                     get_template)
from .clean_pipelines import clean_pipelines
from .renumerate_stages import renumerate_stages


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

    def post_pipeline(self, pipeline):
        """Send Pipeline JSON to Spinnaker."""
        url = "{0}/pipelines".format(API_URL)

        if isinstance(pipeline, str):
            pipeline_json = pipeline
        else:
            pipeline_json = json.dumps(pipeline)

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

    def render_wrapper(self, region='us-east-1'):
        """Generate the base Pipeline wrapper.

        Args:
            region (str): AWS Region.

        Returns:
            dict: Rendered Pipeline wrapper.
        """
        data = {'app': {
            'appname': self.app_name,
            'region': region,
            'triggerjob': self.app_info['triggerjob'],
        }}

        wrapper = get_template(
            template_file='pipeline-templates/pipeline_wrapper.json',
            data=data)

        return json.loads(wrapper)

    def create_pipeline(self):
        """Send a POST to spinnaker to create a new security group."""
        clean_pipelines(app=self.app_name, settings=self.settings)

        self.log.info('Creating wrapper template')
        self.log.debug('Envs: %s', self.settings['pipeline']['env'])

        regions_envs = collections.defaultdict(list)
        for env in self.settings['pipeline']['env']:
            for region in self.settings[env]['regions']:
                regions_envs[region].append(env)
        self.log.info('Environments and Regions for Pipelines: %s',
                      regions_envs)

        pipelines = {}
        for region, envs in regions_envs.items():
            # TODO: Overrides for an environment no longer makes sense. Need to
            # provide override for entire Region possibly.
            pipelines[region] = self.render_wrapper(region=region)

            previous_env = None
            for env in envs:
                try:
                    block = self.construct_pipeline_block(
                        env=env,
                        previous_env=previous_env,
                        region=region)

                    pipelines[region]['stages'].extend(json.loads(block))

                    previous_env = env
                except SpinnakerSubnetError:
                    pass

        self.log.debug('Assembled Pipelines:\n%s', pformat(pipelines))

        for region, pipeline in pipelines.items():
            renumerate_stages(pipeline)

            self.log.info('Updating Pipeline for %s.', region)
            self.post_pipeline(pipeline)

        return True

    def construct_pipeline_block(
            self, env='', previous_env=None,
            region='us-east-1'):
        """Create the Pipeline JSON from template.

        Args:
            env (str): Deploy environment name, e.g. dev, stage, prod.
            previous_env (str): The previous deploy environment to use as
                Trigger.
            region (str): AWS Region to deploy to.

        Returns:
            dict: Pipeline JSON template rendered with configurations.
        """
        self.app_info[env] = self.settings[env]
        self.log.info('Create Pipeline for %s in %s.', env, region)

        self.log.debug('App info:\n%s', self.app_info)

        if env.startswith('prod'):
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
            'encoded_user_data': generate_encoded_user_data(
                env=env,
                region=region,
                app_name=self.app_name,
                group_name=self.group_name),
        })

        pipeline_json = get_template(template_file=template_name, data=data)
        return pipeline_json
