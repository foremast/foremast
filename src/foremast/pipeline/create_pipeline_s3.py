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
from pprint import pformat

from ..utils import get_template
from ..consts import DEFAULT_RUN_AS_USER
from .clean_pipelines import clean_pipelines
from .construct_pipeline_block_s3 import construct_pipeline_block_s3
from .create_pipeline import SpinnakerPipeline
from .renumerate_stages import renumerate_stages


class SpinnakerPipelineS3(SpinnakerPipeline):
    """Manipulate Spinnaker Pipelines.

    Args:
        app (str): Application name.
        trigger_job (str): Jenkins trigger job.
        base (str): Base image name (i.e: fedora).
        prop_path (str): Path to the raw.properties.json.
    """

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
        deploy_type = self.settings['pipeline']['type']
        pipeline_id = self.compare_with_existing(region=region)

        data = {
            'app': {
                'appname': self.app_name,
                'base': base,
                'deploy_type': deploy_type,
                'environment': 'packaging',
                'region': region,
                'triggerjob': self.trigger_job,
                'run_as_user': DEFAULT_RUN_AS_USER,
                'email': email,
                'slack': slack,
                'pipeline': self.settings['pipeline']
            },
            'id': pipeline_id
        }

        self.log.debug('Wrapper app data:\n%s', pformat(data))

        wrapper = get_template(template_file='pipeline/pipeline_wrapper.json.j2', data=data, formats=self.generated)

        return json.loads(wrapper)

    def create_pipeline(self):
        """Main wrapper for pipeline creation.
        1. Runs clean_pipelines to clean up existing ones
        2. determines which environments the pipeline needs
        3. Renders all of the pipeline blocks as defined in configs
        4. Runs post_pipeline to create pipeline
        """
        clean_pipelines(app=self.app_name, settings=self.settings)

        pipeline_envs = self.environments
        self.log.debug('Envs from pipeline.json: %s', pipeline_envs)

        regions_envs = collections.defaultdict(list)
        for env in pipeline_envs:
            for region in self.settings[env]['regions']:
                regions_envs[region].append(env)
        self.log.info('Environments and Regions for Pipelines:\n%s', json.dumps(regions_envs, indent=4))

        pipelines = {}
        for region, envs in regions_envs.items():
            # TODO: Overrides for an environment no longer makes sense. Need to
            # provide override for entire Region possibly.
            pipelines[region] = self.render_wrapper(region=region)

            previous_env = None
            for env in envs:

                block = construct_pipeline_block_s3(
                    env=env,
                    generated=self.generated,
                    previous_env=previous_env,
                    region=region,
                    settings=self.settings[env][region],
                    pipeline_data=self.settings['pipeline'])
                pipelines[region]['stages'].extend(json.loads(block))

                previous_env = env

        self.log.debug('Assembled Pipelines:\n%s', pformat(pipelines))

        for region, pipeline in pipelines.items():
            renumerate_stages(pipeline)

            self.post_pipeline(pipeline)

        return True
