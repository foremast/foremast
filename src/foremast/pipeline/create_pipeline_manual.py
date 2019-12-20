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
"""Create manual Pipeline for Spinnaker."""
import json
import jinja2


from ..consts import TEMPLATES_PATH
from ..utils import get_pipeline_id, normalize_pipeline_name
from ..utils.lookups import FileLookup
from .create_pipeline import SpinnakerPipeline
from .jinja_functions import get_jinja_functions, get_jinja_variables


class SpinnakerPipelineManual(SpinnakerPipeline):
    """Manual JSON configured Spinnaker Pipelines."""

    def create_pipeline(self):
        """Use JSON files to create Pipelines."""

        pipelines = self.settings['pipeline']['pipeline_files']
        self.log.info('Uploading manual Pipelines: %s', pipelines)

        for i, file_name in enumerate(pipelines):

            json_string = self.get_pipeline_file_contents(file_name)

            # If this is a .j2 file render is template, otherwise treat as normal json file
            is_jinja_template = False
            if file_name.endswith(".j2"):
                is_jinja_template = True
                pipeline_vars = self.get_pipeline_variables_dict(i)
                try:
                    json_string = self.get_rendered_json(json_string, pipeline_vars).strip()
                # Catch all exceptions (we don't know what errors the jinja2 user code may throw)
                # Add logging, then re-raise
                except Exception:
                    log_message = "Exception raised during Jinja 2 template rendering.  Check syntax in templates."
                    self.log.exception(log_message)
                    raise
                self.log.info("Jinja2 template successfully rendered")

            try:
                pipelines = json.loads(json_string)
                # result may be a single pipeline object, or list of pipeline objects
                # if a single pipeline object, transform to list with one pipeline object inside
                if not isinstance(pipelines, list):
                    self.log.debug("single pipeline object rendered, transforming to list")
                    pipelines = [pipelines]

            except json.JSONDecodeError:
                # Helpful debugging logging, then re-raise fatal exception
                if is_jinja_template:
                    self.log.error("JSONDecodeError parsing rendered Jinja template, verify it produces valid json")
                    self.log.debug(json_string)
                else:
                    self.log.error("JSONDecodeError parsing json, verify template is vaild json")
                raise

            # Create all pipelines
            for pipeline_dict in pipelines:
                pipeline_dict.setdefault('application', self.app_name)
                pipeline_dict.setdefault('name',
                                         normalize_pipeline_name(name=file_name.lstrip("templates://")))
                pipeline_dict.setdefault('id', get_pipeline_id(app=pipeline_dict['application'],
                                                               name=pipeline_dict['name']))
                self.post_pipeline(pipeline_dict)

        return True

    def get_pipeline_file_contents(self, file_name):
        """Returns a string containing the file constants of the file passed in
        Supports local files, files in git and shared templates in the TEMPLATES_PATH

        Args:
            file_name (str): pipeline file name

        Returns:
            str: Contents of pipeline file."""
        # Check if this file is a shared template in the TEMPLATES_PATH
        if file_name.startswith("templates://"):
            if TEMPLATES_PATH is None:
                raise Exception("Cannot use templates:// schema without TEMPLATES_PATH")
            file_name = file_name.lstrip("templates://")
            pipeline_templates_path = TEMPLATES_PATH.rstrip("/") + "/pipeline"
            lookup = FileLookup(git_short=None, runway_dir=pipeline_templates_path)
        else:
            # Consider it a local repo file, check local or git:
            lookup = FileLookup(git_short=self.generated.gitlab()['main'], runway_dir=self.runway_dir)

        return lookup.get(filename=file_name)

    def get_rendered_json(self, json_string, pipeline_vars=None):
        """Takes a string of a manual template and renders it as a Jinja2 template, returning the result

        Args:
            json_string (str): pipeline in jinja/json format
            pipeline_vars (dict): key/value pairs of variables the pipline expects

        Returns:
            str: pipeline json after Jinja is rendered"""

        try:
            if TEMPLATES_PATH:
                loader = jinja2.FileSystemLoader(TEMPLATES_PATH)
            else:
                loader = jinja2.BaseLoader()

            jinja_template = jinja2.Environment(loader=loader).from_string(json_string)
            # Get any pipeline args defined in pipeline.json, default to empty dict if none defined
            pipeline_args = dict()
        except jinja2.TemplateNotFound:
            # Log paths searched for debugging, then re-raise
            message = 'Jinja2 TemplateNotFound exception in paths {paths}'.format(paths=loader.searchpath)
            self.log.error(message)
            raise

        # Expose permitted functions and variables to the template
        pipeline_args.update(get_jinja_functions())
        pipeline_args.update(get_jinja_variables(self))

        # If any args set in the pipeline file add them to the pipeline_args.variables
        if pipeline_vars is not None:
            pipeline_args["template_variables"] = pipeline_vars

        # Render the template
        return jinja_template.render(pipeline_args)

    def get_pipeline_variables_dict(self, index):
        """Safely gets the user defined variables from the pipeline.json file

        Args:
            index (int): index of pipeline defined in pipeline.json

        Returns:
            dict: key/value pair of variables defined in pipeline.json"""

        # Safely get variables out of pipeline.json if they are set
        pipe_settings = self.settings["pipeline"]
        if "template_variables" in pipe_settings \
           and isinstance(pipe_settings["template_variables"], list) \
           and len(pipe_settings["template_variables"]) > index:
            return pipe_settings["template_variables"][index]

        # Default value is None
        return None
