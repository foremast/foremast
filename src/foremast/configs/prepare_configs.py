"""Prepare the Application Configurations."""
import collections
import json
import logging
import os
from base64 import b64decode

import gitlab

from ..consts import GIT_URL

ENVS = ('build', 'dev', 'stage', 'prod', 'prodp', 'stagepci', 'prods', 'stagesox')
LOG = logging.getLogger(__name__)


def process_git_configs(git_short='', token_file=''):
    """Retrieve _application.json_ files from GitLab.

    Args:
        git_short (str): Short Git representation of repository, e.g.
            forrest/core.
        token_file (str): Name of file with GitLab private token.

    Returns:
        collections.defaultdict: Configurations stored for each environment
        found.
    """
    LOG.info('Processing application.json files from GitLab.')

    with open(token_file, 'rt') as token_handle:
        token = token_handle.read().strip()

    server = gitlab.Gitlab(GIT_URL, token=token)

    project_id = server.getproject(git_short)['id']

    app_configs = collections.defaultdict(dict)
    for env in ENVS:
        file_blob = server.getfile(
            project_id,
            'runway/application-master-{env}.json'.format(env=env),
            'master')
        LOG.debug('GitLab file response:\n%s', file_blob)

        if not file_blob:
            LOG.debug('Application configuration not available for %s.', env)
            # TODO: Use default configs anyways?
            continue
        else:
            file_contents = b64decode(file_blob['content'])
            app_configs[env] = json.loads(file_contents.decode())

    config_commit = server.getbranch(project_id, 'master')['commit']['id']
    app_configs['pipeline']['config_commit'] = config_commit

    LOG.info('Processing pipeline.json from GitLab.')
    pipeline_blob = server.getfile(project_id,
                                   'runway/pipeline.json',
                                   'master', )

    if not pipeline_blob:
        LOG.info('Pipeline configuration not available, using defaults.')
        app_configs['pipeline'] = {'env': ['stage', 'prod']}
    else:
        LOG.info('Pipeline configuration found.')
        pipeline_contents = b64decode(pipeline_blob['content'])
        LOG.info(pipeline_contents.decode())
        app_configs['pipeline'] = json.loads(pipeline_contents.decode())
        if 'env' not in app_configs['pipeline']:
            app_configs['pipeline']['env'] = ['stage', 'prod']

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
    LOG.info('Processing application.json files from local directory.')

    app_configs = collections.defaultdict(dict)
    for env in ENVS:
        file_name = os.path.join(runway_dir,
                                 'application-master-{env}.json'.format(
                                     env=env))
        LOG.debug('File to read: %s', file_name)

        try:
            with open(file_name, 'rt') as json_file:
                LOG.info('Processing %s.', file_name)
                app_configs[env] = json.load(json_file)
        except FileNotFoundError:
            continue

    LOG.info('Processing pipeline.json from local directory')
    try:
        pipeline_file = os.path.join(runway_dir, 'pipeline.json')
        LOG.debug('Reading pipeline.json from %s', pipeline_file)
        with open(pipeline_file) as pipeline:
            app_configs['pipeline'] = json.load(pipeline)

        if 'env' not in app_configs['pipeline']:
            app_configs['pipeline']['env'] = ['stage', 'prod']
    except FileNotFoundError:
        LOG.warning('Unable to process pipeline.json. Using defaults.')
        app_configs['pipeline'] = {'env': ['stage', 'prod']}

    LOG.debug('Application configs:\n%s', app_configs)
    return app_configs
