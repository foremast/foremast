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

"""Create onetime Pipelines for Spinnaker.

These are circumventions for redployments to a specific Environment in a Region.
"""
import json

from .create_pipeline import SpinnakerPipeline


class SpinnakerPipelineOnetime(SpinnakerPipeline):
    """Manipulate Spinnaker Pipelines.

    Args:
        app (str): Application name.
        trigger_job (str): Jenkins trigger job.
        base (str): Base image name (i.e: fedora).
        prop_path (str): Path to the raw.properties.json.
        onetime (str): Environment to build onetime pipeline for.
    """

    def __init__(self,
                 app='',
                 trigger_job='',
                 prop_path='',
                 base='',
                 onetime=''):
        super().__init__(app=app,
                         trigger_job=trigger_job,
                         prop_path=prop_path,
                         base=base)
        self.environments = [onetime]

    def post_pipeline(self, pipeline):
        """Send Pipeline JSON to Spinnaker.

        Args:
            pipeline (dict, str): New Pipeline to create.
        """
        if isinstance(pipeline, str):
            pipeline_str = pipeline
        else:
            pipeline_str = json.dumps(pipeline)

        pipeline_json = json.loads(pipeline_str)

        # Note pipeline name is manual
        name = '{0} (onetime-{1})'.format(pipeline_json['name'],
                                          self.environments[0])
        pipeline_json['name'] = name

        # disable trigger as not to accidently kick off multiple deployments
        for trigger in pipeline_json['triggers']:
            trigger['enabled'] = False

        self.log.debug('Manual Pipeline JSON:\n%s', pipeline_json)
        super().post_pipeline(pipeline_json)
