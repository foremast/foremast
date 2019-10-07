#   Foremast - Pipeline Tooling
#
#   Copyright 2018 Gogo, LLC
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

from ..consts import DEFAULT_RUN_AS_USER, EC2_PIPELINE_TYPES
from ..exceptions import SpinnakerPipelineCreationFailed
from ..utils import ami_lookup, generate_packer_filename, get_details, get_properties, get_subnets, get_template
from ..utils.gate import gate_request
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
        runway_dir (str): Path to local runway directory.
    """

    def __init__(self, app='', trigger_job='', prop_path='', base='', runway_dir=''):
        self.log = logging.getLogger(__name__)

        self.header = {'content-type': 'application/json'}
        self.here = os.path.dirname(os.path.realpath(__file__))

        self.runway_dir = os.path.expandvars(os.path.expanduser(runway_dir or ''))

        self.base = base
        self.trigger_job = trigger_job
        self.generated = get_details(app=app)
        self.app_name = self.generated.app_name()
        self.group_name = self.generated.project
        self.repo_name = self.generated.repo

        self.settings = get_properties(prop_path)
        self.environments = self.settings['pipeline']['env']

    def post_pipeline(self, pipeline):
        """Send Pipeline JSON to Spinnaker.

        Args:
            pipeline (json): json of the pipeline to be created in Spinnaker
        """
        uri = '/pipelines'

        if isinstance(pipeline, str):
            pipeline_json = pipeline
        else:
            pipeline_json = json.dumps(pipeline)

        pipeline_dict = json.loads(pipeline_json)

        self.log.debug('Pipeline JSON:\n%s', pipeline_json)

        pipeline_response = gate_request(method='POST', uri=uri, data=pipeline_json, headers=self.header)

        self.log.debug('Pipeline creation response:\n%s', pipeline_response.text)

        if not pipeline_response.ok:
            raise SpinnakerPipelineCreationFailed('Pipeline for {0}: {1}'.format(self.app_name,
                                                                                 pipeline_response.json()))

        self.log.info('Successfully created "%s" pipeline in application "%s".', pipeline_dict['name'],
                      pipeline_dict['application'])

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
        bake_instance_type = self.settings['pipeline']['image']['bake_instance_type']

        ami_id = ami_lookup(name=base, region=region)

        ami_template_file = generate_packer_filename(provider, region, baking_process)

        pipeline_id = self.compare_with_existing(region=region)

        data = {
            'app': {
                'ami_id': ami_id,
                'appname': self.app_name,
                'group_name': self.group_name,
                'repo_name': self.repo_name,
                'base': base,
                'environment': 'packaging',
                'region': region,
                'triggerjob': self.trigger_job,
                'run_as_user': DEFAULT_RUN_AS_USER,
                'email': email,
                'slack': slack,
                'root_volume_size': root_volume_size,
                'bake_instance_type': bake_instance_type,
                'ami_template_file': ami_template_file,
                'pipeline': self.settings['pipeline']
            },
            'id': pipeline_id
        }

        self.log.debug('Wrapper app data:\n%s', pformat(data))

        wrapper = get_template(template_file='pipeline/pipeline_wrapper.json.j2', data=data, formats=self.generated)

        return json.loads(wrapper)

    def get_existing_pipelines(self):
        """Get existing pipeline configs for specific application.

        Returns:
            str: Pipeline config json

        """
        uri = "/applications/{0}/pipelineConfigs".format(self.app_name)
        resp = gate_request(uri=uri)
        assert resp.ok, 'Failed to lookup pipelines for {0}: {1}'.format(self.app_name, resp.text)

        return resp.json()

    def compare_with_existing(self, region='us-east-1', onetime=False):
        """Compare desired pipeline with existing pipelines.

        Args:
            region (str): Region of desired pipeline.
            onetime (bool): Looks for different pipeline if Onetime

        Returns:
            str: pipeline_id if existing, empty string of not.

        """
        pipelines = self.get_existing_pipelines()
        pipeline_id = None
        found = False
        for pipeline in pipelines:
            correct_app_and_region = (pipeline['application'] == self.app_name) and (region in pipeline['name'])
            if onetime:
                onetime_str = "(onetime-{})".format(self.environments[0])
                if correct_app_and_region and onetime_str in pipeline['name']:
                    found = True
            elif correct_app_and_region:
                found = True

            if found:
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
        self.log.info('Environments and Regions for Pipelines:\n%s', json.dumps(regions_envs, indent=4))

        subnets = None
        pipelines = {}
        for region, envs in regions_envs.items():
            self.generated.data.update({
                'region': region,
            })

            # TODO: Overrides for an environment no longer makes sense. Need to
            # provide override for entire Region possibly.
            pipelines[region] = self.render_wrapper(region=region)

            previous_env = None
            for env in envs:
                self.generated.data.update({
                    'env': env,
                })

                pipeline_block_data = {
                    "env": env,
                    "generated": self.generated,
                    "previous_env": previous_env,
                    "region": region,
                    "settings": self.settings[env][region],
                    "pipeline_data": self.settings['pipeline'],
                }

                if self.settings['pipeline']['type'] in EC2_PIPELINE_TYPES:
                    if not subnets:
                        subnets = get_subnets()
                    try:
                        region_subnets = {region: subnets[env][region]}
                    except KeyError:
                        self.log.info('%s is not available for %s.', env, region)
                        continue
                    pipeline_block_data['region_subnets'] = region_subnets

                block = construct_pipeline_block(**pipeline_block_data)
                pipelines[region]['stages'].extend(json.loads(block))
                previous_env = env

        self.log.debug('Assembled Pipelines:\n%s', pformat(pipelines))

        for region, pipeline in pipelines.items():
            renumerate_stages(pipeline)

            self.post_pipeline(pipeline)

        return True
