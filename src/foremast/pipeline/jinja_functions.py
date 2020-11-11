#   Foremast - Pipeline Tooling
#
#   Copyright 2019 Redbox Automated Retail, LLC
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
"""Functions and variables that can be exposed to Jinja2 templates"""

from ..utils.kayenta import get_canary_id
from ..utils.pipelines import get_pipeline_id, generate_predictable_pipeline_id


def get_jinja_functions():
    """Gets a dictionary of functions that can be exposed to Jinja templates"""
    functions = dict()
    functions[get_canary_id.__name__] = get_canary_id
    functions[get_pipeline_id.__name__] = get_pipeline_id
    functions[raise_exception.__name__] = raise_exception
    functions[generate_predictable_pipeline_id.__name__] = generate_predictable_pipeline_id

    return functions


def get_jinja_variables(pipeline):
    """Gets a dictionary of variables from a SpinnakerPipeline that can be exposed to Jinja templates"""
    variables = dict()
    # Deprecated variables: Use the app block instead
    variables["trigger_job"] = pipeline.trigger_job
    variables["group_name"] = pipeline.group_name
    variables["app_name"] = pipeline.app_name
    variables["repo_name"] = pipeline.repo_name
    # Deprecated end

    email = pipeline.settings['pipeline']['notifications']['email']
    slack = pipeline.settings['pipeline']['notifications']['slack']
    deploy_type = pipeline.settings['pipeline']['type']

    # Replaces top level variables above which are deprecated
    # app block matches non-manual pipeline types like ec2, lambda, etc for consistency
    variables["data"] = {
        'app': {
            'appname': pipeline.app_name,
            'group_name': pipeline.group_name,
            'repo_name': pipeline.repo_name,
            'deploy_type': deploy_type,
            'environment': 'packaging',
            'triggerjob': pipeline.trigger_job,
            'email': email,
            'slack': slack,
            'pipeline': pipeline.settings['pipeline']
        }
    }

    return variables


def raise_exception(message):
    """A function for raising an exception from inside a Jinja Template"""
    raise Exception(message)
