#   Foremast - Pipeline Tooling
#
#   Copyright 2016 Gogo, LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""Create Pipelines for Spinnaker."""
import collections
import json
import logging
import os
from pprint import pformat

import requests

from ..consts import API_URL, GATE_CLIENT_CERT, GATE_CA_BUNDLE
from ..exceptions import SpinnakerPipelineCreationFailed
from ..utils import (ami_lookup, get_details, get_properties, get_subnets,
                     get_template, generate_packer_filename)
from .clean_pipelines import clean_pipelines
from .construct_pipeline_block import construct_pipeline_block
from .renumerate_stages import renumerate_stages


class SpinnakerPipeline:
    """Manipulate Spinnaker Pipelines.

    Args:
        app (str): Application name.
        trigger_job (str): Jenkins trigger job.
        base (str): Base image name (i.e: fedora).
        prop_path (str): Path to the raw.properties.json.
    """

    def __init__(self,
                 app='',
                 trigger_job='',
                 prop_path='',
                 base=''):
        self.log = logging.getLogger(__name__)

        self.header = {'content-type': 'application/json'}
        self.here = os.path.dirname(os.path.realpath(__file__))

        self.base = base
        self.trigger_job = trigger_job
        self.generated = get_details(app=app)
        self.app_name = self.generated.app_name()
        self.group_name = self.generated.project

        self.settings = get_properties(prop_path)
        self.environments = self.settings['pipeline']['env']

    def post_pipeline(self, pipeline):
        """Send Pipeline JSON to Spinnaker.

        Args:
            pipeline (json): json of the pipeline to be created in Spinnaker
        """
        url = "{0}/pipelines".format(API_URL)

        if isinstance(pipeline, str):
            pipeline_json = pipeline
        else:
            pipeline_json = json.dumps(pipeline)

        self.log.debug('Pipeline JSON:\n%s', pipeline_json)

        pipeline_response = requests.post(url,
                                          data=pipeline_json,
                                          headers=self.header,
                                          verify=GATE_CA_BUNDLE,
                                          cert=GATE_CLIENT_CERT)

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

        This renders the non-repeatable stages in a pipeline, like jenkins, baking, tagging and notifications.

        Args:
            region (str): AWS Region.

        Returns:
            dict: Rendered Pipeline wrapper.
        """
        base = self.settings['pipeline']['base']

        if self.base:
            base = self.base

        email = self.settings['pipeline']['notifications']['email']
        slack = self.settings['pipeline']['notifications']['slack']
        baking_process = self.settings['pipeline']['image']['builder']
        provider = 'aws'
        root_volume_size = self.settings['pipeline']['image']['root_volume_size']

        if root_volume_size > 50:
            raise SpinnakerPipelineCreationFailed(
                'Setting "root_volume_size" over 50G is not allowed. We found {0}G in your configs.'.format(
                    root_volume_size))

        ami_id = ami_lookup(name=base,
                            region=region)

        ami_template_file = generate_packer_filename(provider, region, baking_process)

        pipeline_id = self.compare_with_existing(region=region)

        data = {
            'app': {
                'ami_id': ami_id,
                'appname': self.app_name,
                'base': base,
                'environment': 'packaging',
                'region': region,
                'triggerjob': self.trigger_job,
                'email': email,
                'slack': slack,
                'root_volume_size': root_volume_size,
                'ami_template_file': ami_template_file,
            },
            'id': pipeline_id
        }

        self.log.debug('Wrapper app data:\n%s', pformat(data))

        wrapper = get_template(
            template_file='pipeline/pipeline_wrapper.json.j2',
            data=data)

        return json.loads(wrapper)

    def get_existing_pipelines(self):
        """Get existing pipeline configs for specific application.

        Returns:
            str: Pipeline config json
        """
        url = "{0}/applications/{1}/pipelineConfigs".format(API_URL, self.app_name)
        resp = requests.get(url,
                            verify=GATE_CA_BUNDLE,
                            cert=GATE_CLIENT_CERT)
        assert resp.ok, 'Failed to lookup pipelines for {0}: {1}'.format(
            self.app_name, resp.text)

        return resp.json()

    def compare_with_existing(self, region='us-east-1'):
        """Compare desired pipeline with existing pipelines.

        Args:
            region (str): Region of desired pipeline.

        Returns:
            str: pipeline_id if existing, empty string of not.
        """
        pipelines = self.get_existing_pipelines()
        pipeline_id = ''
        for pipeline in pipelines:
            if (pipeline['application'] == self.app_name) and (region in pipeline['name']):
                self.log.info('Existing pipeline found - %s', pipeline['name'])
                pipeline_id = pipeline['id']
                break
        else:
            self.log.info('No existing pipeline found')

        return pipeline_id

    def create_pipeline(self):
        """Main wrapper for pipeline creation.
        1. Runs clean_pipelines to clean up existing ones
        2. determines which environments the pipeline needs
        3. gets all subnets for template rendering
        4. Renders all of the pipeline blocks as defined in configs
        5. Runs post_pipeline to create pipeline
        """
        clean_pipelines(app=self.app_name, settings=self.settings)

        pipeline_envs = self.environments
        self.log.debug('Envs from pipeline.json: %s', pipeline_envs)

        regions_envs = collections.defaultdict(list)
        for env in pipeline_envs:
            for region in self.settings[env]['regions']:
                regions_envs[region].append(env)
        self.log.info('Environments and Regions for Pipelines:\n%s',
                      json.dumps(regions_envs, indent=4))

        subnets = get_subnets()

        pipelines = {}
        for region, envs in regions_envs.items():
            # TODO: Overrides for an environment no longer makes sense. Need to
            # provide override for entire Region possibly.
            pipelines[region] = self.render_wrapper(region=region)

            previous_env = None
            for env in envs:
                try:
                    region_subnets = {region: subnets[env][region]}
                except KeyError:
                    self.log.info('%s is not available for %s.', env, region)
                    continue

                block = construct_pipeline_block(
                    env=env,
                    generated=self.generated,
                    previous_env=previous_env,
                    region=region,
                    region_subnets=region_subnets,
                    settings=self.settings[env],
                    pipeline_data=self.settings['pipeline'])

                pipelines[region]['stages'].extend(json.loads(block))

                previous_env = env

        self.log.debug('Assembled Pipelines:\n%s', pformat(pipelines))

        for region, pipeline in pipelines.items():
            renumerate_stages(pipeline)

            self.post_pipeline(pipeline)

        return True
