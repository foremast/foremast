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

"""Write output files for configurations."""
import json
import logging
from pprint import pformat

import gogoutils

from ..consts import APP_FORMATS
from ..utils import DeepChainMap, get_template

LOG = logging.getLogger(__name__)


def convert_ini(config_dict):
    """Convert _config_dict_ into a list of INI formatted strings.

    Args:
        config_dict (dict): Configuration dictionary to be flattened.

    Returns:
        (list) Lines to be written to a file in the format of KEY1_KEY2=value.
    """
    config_lines = []

    for env, configs in sorted(config_dict.items()):
        for resource, app_properties in sorted(configs.items()):
            try:
                for app_property, value in sorted(app_properties.items()):
                    variable = '{env}_{resource}_{app_property}'.format(
                        env=env,
                        resource=resource,
                        app_property=app_property).upper()

                    if isinstance(value, (dict, DeepChainMap)):
                        safe_value = "'{0}'".format(json.dumps(dict(value)))
                    else:
                        safe_value = json.dumps(value)

                    line = "{variable}={value}".format(variable=variable,
                                                       value=safe_value)

                    LOG.debug('INI line: %s', line)
                    config_lines.append(line)
            except AttributeError:
                resource = resource.upper()
                app_properties = "'{}'".format(json.dumps(app_properties))
                line = '{0}={1}'.format(resource, app_properties)

                LOG.debug('INI line: %s', line)
                config_lines.append(line)
    return config_lines


def write_variables(app_configs=None, out_file='', git_short=''):
    """Append _application.json_ configs to _out_file_, .exports, and .json.

    Variables are written in INI style, e.g. UPPER_CASE=value. The .exports file
    contains 'export' prepended to each line for easy sourcing. The .json file
    is a minified representation of the combined configurations.

    Args:
        app_configs (dict): Environment configurations from _application.json_
            files, e.g. {'dev': {'elb': {'subnet_purpose': 'internal'}}}.
        out_file (str): Name of INI file to append to.
        git_short (str): Short name of Git repository, e.g. forrest/core.

    Returns:
        dict: Configuration equivalent to the JSON output.
    """
    generated = gogoutils.Generator(*gogoutils.Parser(git_short).parse_url(),
                                    formats=APP_FORMATS)

    json_configs = {}
    for env, configs in app_configs.items():
        if env is not 'pipeline':
            instance_profile = generated.iam()['profile']
            rendered_configs = json.loads(
                get_template('configs/configs.json.j2',
                             env=env,
                             app=generated.app_name(),
                             profile=instance_profile))
            json_configs[env] = dict(DeepChainMap(configs, rendered_configs))
        else:
            default_pipeline_json = json.loads(get_template(
                'configs/pipeline.json.j2'))
            json_configs['pipeline'] = dict(DeepChainMap(
                configs, default_pipeline_json))

    LOG.debug('Compiled configs:\n%s', pformat(json_configs))

    config_lines = convert_ini(json_configs)

    with open(out_file, 'at') as jenkins_vars:
        LOG.info('Appending variables to %s.', out_file)
        jenkins_vars.write('\n'.join(config_lines))

    with open(out_file + '.exports', 'wt') as export_vars:
        LOG.info('Writing sourceable variables to %s.', export_vars.name)
        export_vars.write('\n'.join('export {0}'.format(line)
                                    for line in config_lines))

    with open(out_file + '.json', 'wt') as json_handle:
        LOG.info('Writing JSON to %s.', json_handle.name)
        LOG.debug('Total JSON dict:\n%s', json_configs)
        json.dump(json_configs, json_handle)

    return json_configs
