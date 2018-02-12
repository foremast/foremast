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
"""Prepare the Application Configurations."""
import collections
import logging

from ..consts import ENVS
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

    app_configs = collections.defaultdict(dict)
    for env in ENVS:
        app_json = 'runway/application-master-{env}.json'.format(env=env)
        try:
            env_config = file_lookup.json(filename=app_json)
            app_configs[env] = apply_region_configs(env_config)
        except FileNotFoundError:
            LOG.critical('Application configuration not available for %s.', env)
            # TODO: Use default configs anyways?
            continue

    LOG.info('Processing pipeline.json from GitLab.')

    pipeline_json = 'runway/pipeline.json'
    try:
        app_configs['pipeline'] = file_lookup.json(filename=pipeline_json)
        LOG.info('Pipeline configuration found.')
    except FileNotFoundError:
        LOG.info('Pipeline configuration not available, using defaults.')
        app_configs['pipeline'] = {'env': ['stage', 'prod']}

    # FIXME: Check response of .getbranch() is not False before trying to access as dict
    config_commit = file_lookup.server.getbranch(file_lookup.project_id, 'master')['commit']['id']
    LOG.info('Commit ID used: %s', config_commit)
    app_configs['pipeline']['config_commit'] = config_commit

    LOG.debug('Application configs:\n%s', app_configs)
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

    app_configs = collections.defaultdict(dict)
    for env in ENVS:
        file_json = 'application-master-{env}.json'.format(env=env)
        try:
            env_config = file_lookup.json(filename=file_json)
            app_configs[env] = apply_region_configs(env_config)
        except FileNotFoundError:
            LOG.critical('Application configuration not available for %s.', env)
            continue

    LOG.info('Processing pipeline.json from local directory')

    try:
        app_configs['pipeline'] = file_lookup.json(filename='pipeline.json')
    except FileNotFoundError:
        LOG.warning('Unable to process pipeline.json. Using defaults.')
        app_configs['pipeline'] = {'env': ['stage', 'prod']}

    LOG.debug('Application configs:\n%s', app_configs)
    return app_configs

def apply_region_configs(env_config):
    """Override default env configs with region specific configs and nest
    all values under a region
    
    Args:
        env_config (dict): The environ
    
    Return:
        dict: Newly updated dictionary with region overrides applied.
    """
    new_config = env_config.copy() 
    for region in env_config['regions']:
        if isinstance(env_config.get('regions'), dict):
            region_specific_config = env_config['regions'][region]
            new_config[region] = dict(DeepChainMap(region_specific_config, env_config))
            print(new_config)
        else:
            new_config[region] = env_config.copy()
    return new_config