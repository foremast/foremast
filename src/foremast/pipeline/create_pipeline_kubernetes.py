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
import json
from pprint import pformat

from ..utils import get_template
from ..consts import DEFAULT_RUN_AS_USER
# from .clean_pipelines import clean_pipelines
from .construct_pipeline_block_kubernetes import construct_kubernetespipeline
from .create_pipeline import SpinnakerPipeline


class SpinnakerPipelineKubernetesPipeline(SpinnakerPipeline):
    """Manipulate Spinnaker Pipelines.

    Args:
        app (str): Application name.
        trigger_job (str): Jenkins trigger job.
        base (str): Base image name (i.e: fedora).
        prop_path (str): Path to the raw.properties.json.
    """

    def render_wrapper_kubernetes(self, data):
        """Generate the base Pipeline wrapper.

        This renders the non-repeatable stages in a pipeline, like jenkins, baking, tagging and notifications.

        Args:
            region (str): AWS Region.

        Returns:
            dict: Rendered Pipeline wrapper.
        """

        # Contains generic wrapper (non-stage) pipeline configs
        wrapper = get_template(template_file='pipeline/pipeline_wrapper.json.j2', data=data, formats=self.generated)
        wrapper = json.loads(wrapper)
        return wrapper

    def create_pipeline(self):
        """Main wrapper for pipeline creation.
        1. Runs clean_pipelines to clean up existing ones
        2. determines which environments the pipeline needs
        3. Renders all of the pipeline blocks as defined in configs
        4. Runs post_pipeline to create pipeline
        """
        # ToDo: Taken out until we sort out the region/env/account mappings from foremast->spin->k8s
        # clean_pipelines(app=self.app_name, settings=self.settings)

        pipeline_envs = self.environments
        self.log.debug('Envs from pipeline.json: %s', pipeline_envs)

        pipelines = {}
        for env in pipeline_envs:
            template_data = self.generate_template_data(env)
            pipelines[env] = self.render_wrapper_kubernetes(template_data)
            pipeline_template_raw = construct_kubernetespipeline(
                env=env,
                generated=self.generated,
                previous_env=None,
                pipeline_data=self.settings['pipeline'])
            pipeline_template = json.loads(pipeline_template_raw)
            # Merge template and wrapper into 1 pipeline
            pipelines[env].update(pipeline_template)

        self.log.debug('Assembled Pipelines:\n%s', pformat(pipelines))

        for env, pipeline in pipelines.items():
            # ToDo: Determine if renumerate_stages is needed in k8s
            # Needed if we can break each pipeline into seperate stages
            # renumerate_stages(pipeline)
            self.post_pipeline(pipeline)

        return True

    def generate_template_data(self, environment):
        """Generates the data used to populate the Jinja 2 template for each pipeline."""

        region = self.app_name
        email = self.settings['pipeline']['notifications']['email']
        slack = self.settings['pipeline']['notifications']['slack']
        deploy_type = self.settings['pipeline']['type']
        # Pass env in as region when getting an existing pipeline ID
        # This is because in AWS our pipelines are "name [region]" but in k8s they are "name [env/account]"
        pipeline_id = self.compare_with_existing(region=environment)

        data = {
            'app': {
                'appname': self.app_name,
                'group_name': self.group_name,
                'repo_name': self.repo_name,
                'deploy_type': deploy_type,
                'region': region,
                'environment': environment,
                'triggerjob': self.trigger_job,
                'run_as_user': DEFAULT_RUN_AS_USER,
                'email': email,
                'slack': slack,
                'pipeline': self.settings['pipeline']
            },
            'id': pipeline_id
        }

        return data
