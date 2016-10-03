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
"""Lookup AMI ID from a simple name."""
import json
import logging
import os
from base64 import b64decode

import gitlab
import requests

from ..consts import AMI_JSON_URL, GIT_URL, GITLAB_TOKEN

LOG = logging.getLogger(__name__)


def ami_lookup(region='us-east-1', name='tomcat8'):
    """Use _name_ to find AMI ID. If no ami_base_url or gitlab_token is provided,
    _name_ is returned as the ami id

    Args:
        region (str): AWS Region to find AMI ID.
        name (str): Simple AMI base name to lookup.

    Returns:
        str: AMI ID for _name_ in _region_.
    """

    if AMI_JSON_URL:
        LOG.info("Getting AMI from %s", AMI_JSON_URL)
        response = requests.get(AMI_JSON_URL)
        assert response.ok, "Error getting ami info from {}".format(AMI_JSON_URL)

        ami_dict = response.json()
        LOG.debug('Lookup AMI table: %s', ami_dict)
        ami_id = ami_dict[region][name]
    elif GITLAB_TOKEN:
        # TODO: Remove GitLab repository in favour of JSON URL option.
        LOG.info("Getting AMI from Gitlab")
        server = gitlab.Gitlab(GIT_URL, token=GITLAB_TOKEN)
        project_id = server.getproject('devops/ansible')['id']

        ami_blob = server.getfile(project_id, 'scripts/{0}.json'.format(region), 'master')
        ami_contents = b64decode(ami_blob['content']).decode()
        ami_dict = json.loads(ami_contents)
        LOG.debug('Lookup AMI table: %s', ami_dict)
        ami_id = ami_dict[name]
    else:
        ami_id = name

    LOG.info('Using AMI: %s', ami_id)

    return ami_id


class GitLookup():
    """Retrieve files from a GitLab Server.

    Args:
        git_short (str): Short Git representation of repository, e.g.
            forrest/core.
        runway_dir (str): Root of local runway directory to use instead of
            accessing Git.
    """

    def __init__(self, git_short='', runway_dir=''):
        self.runway_dir = os.path.expandvars(os.path.expanduser(runway_dir))

        if not self.runway_dir:
            self.git_short = git_short
            self.server = gitlab.Gitlab(GIT_URL, token=GITLAB_TOKEN)
            self.project_id = self.server.getproject(self.git_short)['id']

    def get(self, branch='master', filename=''):
        """Retrieve _filename_ from GitLab.

        Args:
            branch (str): Git Branch to find file.
            filename (str): Name of file to retrieve relative to root of Git
                repository, or _runway_dir_ if specified.

        Returns:
            str: Contents of file.
        """
        file_contents = ''

        LOG.info('Retrieving "%s" from "%s".', filename, self.runway_dir or self.git_short)

        if self.runway_dir:
            with open(os.path.join(self.runway_dir, filename), 'rt') as lookup_file:
                file_contents = lookup_file.read()
        else:
            file_blob = self.server.getfile(self.project_id, filename, branch)
            LOG.debug('GitLab file response:\n%s', file_blob)

            file_contents = ''

            if not file_blob:
                LOG.warning('"%s" Branch "%s" missing file "%s".', self.git_short, branch, filename)
            else:
                file_contents = b64decode(file_blob['content']).decode()

        LOG.debug('File contents:\n%s', file_contents)
        return file_contents

    def json(self, branch='master', filename=''):
        """Retrieve _filename_ from GitLab.

        Args:
            branch (str): Git Branch to find file.
            filename (str): Name of file to retrieve.

        Returns:
            dict: Decoded JSON.

        Raises:
            SystemExit: Invalid JSON provided.
        """
        file_contents = self.get(branch=branch, filename=filename)

        try:
            json_dict = json.loads(file_contents)
        except json.JSONDecodeError as error:
            msg = ('"{filename}" appears to be invalid json. '
                   'Please validate it with http://jsonlint.com. '
                   'JSON decoder error:\n'
                   '{error}').format(
                       filename=filename, error=error)
            raise SystemExit(msg)

        LOG.debug('JSON object:\n%s', json_dict)
        return json_dict
