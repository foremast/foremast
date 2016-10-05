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
import json
import logging
import os
from base64 import b64decode

import gitlab

from ..consts import ENVS, GIT_URL, GITLAB_TOKEN
from ..utils import GitLookup

LOG = logging.getLogger(__name__)
JSON_ERROR_MSG = '"{0}" appears to be invalid json. Please validate it with http://jsonlint.com.'


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

    file_lookup = GitLookup(git_short=git_short)

    app_configs = collections.defaultdict(dict)
    for env in ENVS:
        app_json = 'runway/application-master-{env}.json'.format(env=env)
        try:
            app_dict = file_lookup.json(filename=app_json)
            app_configs[env] = app_dict
        except FileNotFoundError:
            LOG.debug('Application configuration not available for %s.', env)
            # TODO: Use default configs anyways?
            continue

    LOG.info('Processing pipeline.json from GitLab.')

    pipeline_json = 'runway/pipeline.json'
    try:
        pipeline_dict = file_lookup.json(filename=pipeline_json)
        LOG.info('Pipeline configuration found.')
        app_configs['pipeline'] = pipeline_dict
    except FileNotFoundError:
        LOG.info('Pipeline configuration not available, using defaults.')
        app_configs['pipeline'] = {'env': ['stage', 'prod']}

    config_commit = file_lookup.server.getbranch(file_lookup.roject_id, 'master')['commit']['id']
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
    LOG.info('Processing application.json files from local directory.')

    app_configs = collections.defaultdict(dict)
    for env in ENVS:
        file_json = 'application-master-{env}.json'.format(env=env)
        file_name = os.path.join(runway_dir, file_json)
        LOG.debug('File to read: %s', file_name)

        try:
            with open(file_name, 'rt') as json_file:
                LOG.info('Processing %s.', file_name)
                app_configs[env] = json.load(json_file)
        except FileNotFoundError:
            continue
        except ValueError:
            msg = JSON_ERROR_MSG.format(file_json)
            raise SystemExit(msg)

    LOG.info('Processing pipeline.json from local directory')
    try:
        pipeline_file = os.path.join(runway_dir, 'pipeline.json')
        LOG.debug('Reading pipeline.json from %s', pipeline_file)
        with open(pipeline_file) as pipeline:
            app_configs['pipeline'] = json.load(pipeline)
            LOG.info(app_configs['pipeline'])
    except FileNotFoundError:
        LOG.warning('Unable to process pipeline.json. Using defaults.')
        app_configs['pipeline'] = {'env': ['stage', 'prod']}
    except ValueError:
        msg = JSON_ERROR_MSG.format(pipeline_file)
        raise SystemExit(msg)

    LOG.debug('Application configs:\n%s', app_configs)
    return app_configs
