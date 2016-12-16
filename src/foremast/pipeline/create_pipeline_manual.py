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
"""Create manual Pipeline for Spinnaker."""
from ..utils import get_pipeline_id, normalize_pipeline_name
from ..utils.lookups import FileLookup
from .create_pipeline import SpinnakerPipeline


class SpinnakerPipelineManual(SpinnakerPipeline):
    """Manual JSON configured Spinnaker Pipelines."""

    def create_pipeline(self):
        """Use JSON files to create Pipelines."""
        pipelines = self.settings['pipeline']['pipeline_files']
        self.log.info('Uploading manual Pipelines: %s', pipelines)

        lookup = FileLookup(git_short=self.generated.gitlab()['main'], runway_dir=self.runway_dir)

        for json_file in pipelines:
            json_dict = lookup.json(filename=json_file)

            json_dict.setdefault('application', self.app_name)
            json_dict.setdefault('name', normalize_pipeline_name(name=json_file))

            json_dict.setdefault('id', get_pipeline_id(app=json_dict['application'], name=json_dict['name']))

            self.post_pipeline(json_dict)

        return True
