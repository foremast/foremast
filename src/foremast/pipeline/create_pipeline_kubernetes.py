#   Foremast - Pipeline Tooling
#
#   Copyright 2019 Gogo, LLC
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
import requests
from ..utils import check_managed_pipeline, get_all_pipelines, get_template
from ..exceptions import SpinnakerPipelineCreationFailed
from .clean_pipelines import delete_pipeline
from ..consts import API_URL, GATE_CA_BUNDLE, GATE_CLIENT_CERT, DEFAULT_RUN_AS_USER
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
            data (dict): A dictionary with data to be used in the template

        Returns:
            dict: Rendered Pipeline wrapper.
        """

        # Contains generic wrapper (non-stage) pipeline configs
        wrapper = get_template(template_file='pipeline/pipeline_wrapper.json.j2', data=data, formats=self.generated)
        wrapper = json.loads(wrapper)
        return wrapper

    def create_pipeline(self):
        """Main wrapper for pipeline creation.
        1. Cleans up existing pipelines
        2. Determines which environments and pipelines are needed
        3. Created one pipeline PER environment given
        4. Renders pipeline json from the template matching deployment_type given
        5. Runs post_pipeline for each pipeline generated

        Args:
        Returns:
            bool: True if pipelines were created successfully
        """

        pipeline_envs = self.environments
        self.log.debug('Envs from pipeline.json: %s', pipeline_envs)

        deleted_pipelines = self.clean_kubernetes_pipelines(pipeline_envs)
        self.log.debug('Deleted %s managed pipelines: %s', len(deleted_pipelines), deleted_pipelines)

        pipelines = {}
        for env in pipeline_envs:
            template_data = self.generate_template_data(env)
            pipelines[env] = self.render_wrapper_kubernetes(template_data)
            self.log.debug('Wrapper for env %s: %s', env, pipelines[env])

            k8s_pipeline_type = self.settings['pipeline']['kubernetes']['pipeline_type']
            template_name = 'pipeline/pipeline_kubernetes_{}.json.j2'.format(k8s_pipeline_type)
            self.log.debug('using kubernetes.pipeline_type of "%s", template file "%s"',
                           k8s_pipeline_type, template_name)

            pipeline_json = get_template(template_file=template_name, data=template_data, formats=self.generated)
            pipeline_template = json.loads(pipeline_json)
            # Merge template and wrapper into 1 pipeline
            pipelines[env].update(pipeline_template)

        self.log.debug('Assembled Pipelines:\n%s', pformat(pipelines))

        for env, pipeline in pipelines.items():
            self.post_pipeline(pipeline)

        return True

    def clean_kubernetes_pipelines(self, environments):
        """Deletes pipelines managed by formast that are not included in the current configuration
        1. Checks for pipelines following the convetion: appname [environment]
        2. Checks if the environment is not in the current environment list
        3. If not in the environment list, the pipeline is deleted
        Pipelines not managed by Foremast are ignored
        """
        deleted_pipelines = []
        existing_pipelines = get_all_pipelines(app=self.app_name)
        for pipeline in existing_pipelines:
            pipeline_name = pipeline['name']

            try:
                env = check_managed_pipeline(name=pipeline_name, app_name=self.app_name)
            except ValueError:
                self.log.info('"%s" is not managed.', pipeline_name)
                continue

            self.log.debug('Check "%s" in defined Envs.', env)

            if env not in environments:
                delete_pipeline(app=self.app_name, pipeline_name=pipeline_name)
                deleted_pipelines.append(pipeline_name)

        return deleted_pipelines

    def generate_template_data(self, environment):
        """Generates the data used to populate the Jinja 2 template for each pipeline."""

        region = self.app_name  # k8s in spinnaker region = namespace (use appname instead of default)
        pipeline = self.settings['pipeline']
        email = pipeline['notifications']['email']
        slack = pipeline['notifications']['slack']
        manifest_account = pipeline['kubernetes']['manifest_account_name']
        deploy_type = pipeline['type']
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
                'pipeline': pipeline,
                'manifest_account_name': manifest_account
            },
            'id': pipeline_id
        }

        # If they specified a canary name, add it to the jinja template data
        if 'canaryConfigName' in self.settings['pipeline']['kubernetes'].keys():
            data['canary'] = self.create_canary_config()
        return data

    def create_canary_config(self):
        """Creats a canary config that can be passed to the a J2 template for kayenta canaries
        1. Checks if the pipeline.kubernetes.canaryConfigName setting was set by the user
        2. If set, other canary configuration options like canaryAnalysisIntervalMins is added to the config
        3. The canary config Id is resolved from Spinnaker using the name set by the user
        It is not verified if the current app has the correct permissions to use the canary config requested.
        """
        kube_config = self.settings['pipeline']['kubernetes']
        interval_minutes = kube_config['canaryAnalysisIntervalMins']
        canary_name = kube_config['canaryConfigName']

        canary = {
            'canaryAnalysisIntervalMins': interval_minutes,
            'canaryConfigId': self.get_canary_id(canary_name)
        }

        return canary

    def get_canary_id(self, name):
        """Finds a canary config ID matching the name passed.
        Assumes the canary name is unique and the first match wins.
        """
        url = "{}/v2/canaryConfig".format(API_URL)
        canary_response = requests.get(url, headers=self.header, verify=GATE_CA_BUNDLE, cert=GATE_CLIENT_CERT)

        if not canary_response.ok:
            raise SpinnakerPipelineCreationFailed('Pipeline for {0}: {1}'.format(self.app_name,
                                                                                 canary_response.json()))

        canary_options = canary_response.json()
        names = []
        for config in canary_options:
            names.append(config['name'])
            if config['name'] == name:
                return config['id']

        raise SpinnakerPipelineCreationFailed(
            'Pipeline for {0}: Could not find canary config named {1}.  Options are: {2}'
            .format(self.app_name, name, names))
