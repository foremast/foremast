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


def append_variables(app_configs=None, out_file=''):
    """Append _application.json_ configurations to _out_file_.

    Variables are written in INI style, e.g. UPPER_CASE=value.

    Args:
        app_configs (dict): Environment configurations from _application.json_
            files, e.g. {'dev': {'elb': {'subnet_purpose': 'internal'}}}.
        out_file (str): Name of INI file to append to.

    Returns:
        True upon successful completion.
    """
    with open(out_file, 'at') as jenkins_vars:
        for env, configs in app_configs.items():
            for resource, app_properties in sorted(configs.items()):
                try:
                    for app_property, value in sorted(app_properties.items()):
                        variable = '{env}_{resource}_{app_property}'.format(
                            env=env,
                            resource=resource,
                            app_property=app_property).upper()
                        line = '{variable}={value}'.format(
                            variable=variable,
                            value=json.dumps(value))

                        LOG.debug('INI line: %s', line)

                        jenkins_vars.write('{0}\n'.format(line))
                except AttributeError:
                    continue
    return True


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
        file_contents = b64decode(file_blob['content'])
        app_configs[env] = json.loads(file_contents.decode())

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
