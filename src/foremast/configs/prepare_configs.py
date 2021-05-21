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

from .. import consts
from ..exceptions import ForemastError
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
    app_configs = process_configs(file_lookup,
                                  consts.RUNWAY_BASE_PATH + '/application-master-{env}.json',
                                  consts.RUNWAY_BASE_PATH + '/pipeline.json')
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
        dict: Retrieved application config
    """
    app_configs = collections.defaultdict(dict)
    # Load pipeline config first, determine cloud provider
    # Then load appropriate environment files
    try:
        app_configs['pipeline'] = file_lookup.json(filename=pipeline_config)
    except FileNotFoundError:
        LOG.warning('Unable to process pipeline.json. Using defaults.')
        app_configs['pipeline'] = {'env': ['stage', 'prod']}

    if 'type' in app_configs['pipeline']:
        pipeline_type = app_configs['pipeline']['type']
    else:
        pipeline_type = 'ec2'
    cloud_provider = get_cloud_for_pipeline_type(pipeline_type)
    environments = _get_env_names_for_cloud(cloud_provider)
    LOG.info("Using cloud provider '%s' for pipeline type '%s', supported environments: '%s'",
             cloud_provider, pipeline_type, environments)

    for env in environments:
        file_json = app_config_format.format(env=env)
        try:
            env_config = file_lookup.json(filename=file_json)
            app_configs[env] = apply_region_configs(env_config)
        except FileNotFoundError:
            LOG.critical('Application configuration not available for %s.', env)
            continue

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
    for region in env_config.get('regions', consts.REGIONS):
        if isinstance(env_config.get('regions'), dict):
            region_specific_config = env_config['regions'][region]
            new_config[region] = dict(DeepChainMap(region_specific_config, env_config))
        else:
            new_config[region] = env_config.copy()
    LOG.debug('Region Specific Config:\n%s', new_config)
    return new_config


def get_cloud_for_pipeline_type(pipeline_type):
    """Maps a pipeline type to the corresponding cloud provider

        Args:
            pipeline_type (str): The pipeline type (e.g. cloudfunction, lambda, ec2)

        Return:
            str: The corresponding cloud provider (e.g. aws, gcp)
        """
    if pipeline_type in consts.GCP_TYPES:
        return "gcp"
    elif pipeline_type in consts.AWS_TYPES:
        return "aws"
    else:
        error_message = ("pipeline.type of '{0}' is not supported. "
                         "If this is a manual pipeline it is required you specify the "
                         "pipeline type in AWS_MANUAL_TYPES or GCP_MANUAL_TYPES"
                         ).format(pipeline_type)
        raise ForemastError(error_message)


def _get_env_names_for_cloud(cloud_name):
    """Returns the list of env names for the given cloud

    Args:
        cloud_name, Str: Name of cloud provider.  'aws' and 'gcp' are only supported options.

    Return:
        set: Environment names for the given cloud (e.g. stage, prod) and corresponding configs
    """
    if cloud_name == "aws":
        return consts.ENVS
    elif cloud_name == "gcp":
        # GCP env config is an nested dictionary of env names with config as value
        # only return the names as that is all that is needed, and the AWS config is names only
        return set(consts.GCP_ENVS.keys())
    else:
        raise ValueError("Unknown cloud given while loading cloud environments. Only gcp and aws are acceptable.  "
                         "Received '%s'", cloud_name)
