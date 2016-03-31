"""Prepare the Application Configurations."""
import collections
import json
import logging
import os
from base64 import b64decode

import gitlab

from .utils import get_configs

ENVS = ('dev', 'stage', 'prod')
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

    configs = get_configs(file_name='gitlab.conf')
    server = gitlab.Gitlab(configs['gitlab']['url'], token=token)

    project_id = server.getproject(git_short)['id']

    app_configs = collections.defaultdict(dict)
    for env in ENVS:
        file_blob = server.getfile(
            project_id,
            'runway/application-master-{env}.json'.format(env=env),
            'master')
        LOG.debug('GitLab file response:\n%s', file_blob)

        try:
            file_contents = b64decode(file_blob['content'])
            app_configs[env] = json.loads(file_contents.decode())
        except TypeError:
            continue

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
    for env in ('dev', 'stage', 'prod'):
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

    LOG.debug('Application configs:\n%s', app_configs)
    return app_configs
