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
"""Prepare the Application Configurations."""
import collections
import logging

from ..consts import ENVS, REGIONS
from ..utils import DeepChainMap, FileLookup

LOG = logging.getLogger(__name__)


def process_git_configs(git_short=''):
    """Retrieve _application.json_ files from GitLab.

    Args:
        git_short (str): Short Git representation of repository, e.g.
            forrest/core.

    Returns:
        collections.defaultdict: Configurations stored for each environment
        found.
    """
    LOG.info('Processing application.json files from GitLab "%s".', git_short)
    file_lookup = FileLookup(git_short=git_short)
    app_configs = process_configs(file_lookup, 'runway/application-master-{env}.json', 'runway/pipeline.json')
    commit_obj = file_lookup.project.commits.get('master')
    config_commit = commit_obj.attributes['id']
    LOG.info('Commit ID used: %s', config_commit)
    app_configs['pipeline']['config_commit'] = config_commit
    return app_configs


def process_runway_configs(runway_dir=''):
    """Read the _application.json_ files.

    Args:
        runway_dir (str): Name of runway directory with app.json files.

    Returns:
        collections.defaultdict: Configurations stored for each environment
        found.
    """
    LOG.info('Processing application.json files from local directory "%s".', runway_dir)
    file_lookup = FileLookup(runway_dir=runway_dir)
    app_configs = process_configs(file_lookup, 'application-master-{env}.json', 'pipeline.json')
    return app_configs


def process_configs(file_lookup, app_config_format, pipeline_config):
    """Processes the configs from lookup sources.

    Args:
        file_lookup (FileLookup): Source to look for file/config
        app_config_format (str): The format for application config files.
        pipeline_config (str): Name/path of the pipeline config

    Returns:
        dict: Retreived application config
    """
    app_configs = collections.defaultdict(dict)
    for env in ENVS:
        file_json = app_config_format.format(env=env)
        try:
            env_config = file_lookup.json(filename=file_json)
            app_configs[env] = apply_region_configs(env_config)
        except FileNotFoundError:
            LOG.critical('Application configuration not available for %s.', env)
            continue

    try:
        app_configs['pipeline'] = file_lookup.json(filename=pipeline_config)
    except FileNotFoundError:
        LOG.warning('Unable to process pipeline.json. Using defaults.')
        app_configs['pipeline'] = {'env': ['stage', 'prod']}

    LOG.debug('Application configs:\n%s', app_configs)
    return app_configs


def apply_region_configs(env_config):
    """Override default env configs with region specific configs and nest
    all values under a region

    Args:
        env_config (dict): The environment specific config.

    Return:
        dict: Newly updated dictionary with region overrides applied.
    """
    new_config = env_config.copy()
    for region in env_config.get('regions', REGIONS):
        if isinstance(env_config.get('regions'), dict):
            region_specific_config = env_config['regions'][region]
            new_config[region] = dict(DeepChainMap(region_specific_config, env_config))
        else:
            new_config[region] = env_config.copy()
    LOG.debug('Region Specific Config:\n%s', new_config)
    return new_config
