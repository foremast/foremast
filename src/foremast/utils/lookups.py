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
"""Lookup AMI ID from a simple name."""
import json
import logging
import os
from base64 import b64decode

import gitlab
import requests

from ..consts import AMI_JSON_URL, GIT_URL, GITLAB_TOKEN
from ..exceptions import GitLabApiError
from .warn_user import warn_user

LOG = logging.getLogger(__name__)


def ami_lookup(region='us-east-1', name='tomcat8'):
    """Look up AMI ID.

    Use _name_ to find AMI ID. If no ami_base_url or gitlab_token is provided,
    _name_ is returned as the ami id.

    Args:
        region (str): AWS Region to find AMI ID.
        name (str): Simple AMI base name to lookup.

    Returns:
        str: AMI ID for _name_ in _region_.

    """
    if AMI_JSON_URL:
        ami_dict = _get_ami_dict(AMI_JSON_URL)
        ami_id = ami_dict[region][name]
    elif GITLAB_TOKEN:
        warn_user('Use AMI_JSON_URL feature instead.')
        ami_contents = _get_ami_file(region=region)
        ami_dict = json.loads(ami_contents)
        ami_id = ami_dict[name]
    else:
        ami_id = name

    LOG.info('Using AMI: %s', ami_id)

    return ami_id


def _get_ami_file(region='us-east-1'):
    """Get file from Gitlab.

    Args:
        region (str): AWS Region to find AMI ID.

    Returns:
        str: Contents in json format.

    """
    LOG.info("Getting AMI from Gitlab")
    lookup = FileLookup(git_short='devops/ansible')
    filename = 'scripts/{0}.json'.format(region)
    ami_contents = lookup.remote_file(filename=filename, branch='master')
    LOG.debug('AMI file contents in %s: %s', filename, ami_contents)
    return ami_contents


def _get_ami_dict(json_url):
    """Get ami from a web url.

    Args:
        region (str): AWS Region to find AMI ID.

    Returns:
        dict: Contents in dictionary format.

    """
    LOG.info("Getting AMI from %s", json_url)
    response = requests.get(json_url)
    assert response.ok, "Error getting ami info from {}".format(json_url)
    ami_dict = response.json()
    LOG.debug('AMI json contents: %s', ami_dict)
    return ami_dict


class FileLookup():
    """Retrieve files from a local filesystem or remote GitLab Server.

    When _runway_dir_ is specified, the local directory is given priority and
    remote Git Server will not be used.

    Args:
        git_short (str): Short Git representation of repository, e.g.
            forrest/core.
        runway_dir (str): Root of local runway directory to use instead of
            accessing Git.
    """

    def __init__(self, git_short='', runway_dir=''):
        self.git_short = git_short
        self.runway_dir = os.path.expandvars(os.path.expanduser(runway_dir))

        self.server = None
        self.project = None

        if not self.runway_dir:
            self.get_gitlab_project()

    def get_gitlab_project(self):
        """Get numerical GitLab Project ID.

        Returns:
            int: Project ID number.

        Raises:
            foremast.exceptions.GitLabApiError: GitLab responded with bad status
                code.

        """
        self.server = gitlab.Gitlab(GIT_URL, private_token=GITLAB_TOKEN, api_version=4)
        project = self.server.projects.get(self.git_short)

        if not project:
            raise GitLabApiError('Could not get Project "{0}" from GitLab API.'.format(self.git_short))

        self.project = project
        return self.project

    def local_file(self, filename):
        """Read the local file in _self.runway_dir_.

        Args:
            filename (str): Name of file to retrieve relative to root of
                _runway_dir_.

        Returns:
            str: Contents of local file.

        Raises:
            FileNotFoundError: Requested file missing.

        """
        LOG.info('Retrieving "%s" from "%s".', filename, self.runway_dir)

        file_contents = ''

        file_path = os.path.join(self.runway_dir, filename)

        try:
            with open(file_path, 'rt') as lookup_file:
                file_contents = lookup_file.read()
        except FileNotFoundError:
            LOG.warning('File missing "%s".', file_path)
            raise

        LOG.debug('Local file contents:\n%s', file_contents)
        return file_contents

    def remote_file(self, branch='master', filename=''):
        """Read the remote file on Git Server.

        Args:
            branch (str): Git Branch to find file.
            filename (str): Name of file to retrieve relative to root of
                repository.

        Returns:
            str: Contents of remote file.

        Raises:
            FileNotFoundError: Requested file missing.

        """
        LOG.info('Retrieving "%s" from "%s".', filename, self.git_short)

        file_contents = ''

        try:
            file_blob = self.project.files.get(file_path=filename, ref=branch)
        except gitlab.exceptions.GitlabGetError:
            file_blob = None

        LOG.debug('GitLab file response:\n%s', file_blob)

        if not file_blob:
            msg = 'Project "{0}" is missing file "{1}" in "{2}" branch.'.format(self.git_short, filename, branch)
            LOG.warning(msg)
            raise FileNotFoundError(msg)
        else:
            file_contents = b64decode(file_blob.content).decode()

        LOG.debug('Remote file contents:\n%s', file_contents)
        return file_contents

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

        if self.runway_dir:
            file_contents = self.local_file(filename=filename)
        else:
            file_contents = self.remote_file(branch=branch, filename=filename)

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
        # TODO: Use json.JSONDecodeError when Python 3.4 has been deprecated
        except ValueError as error:
            msg = ('"{filename}" appears to be invalid json. '
                   'Please validate it with http://jsonlint.com. '
                   'JSON decoder error:\n'
                   '{error}').format(
                       filename=filename, error=error)
            raise SystemExit(msg)

        LOG.debug('JSON object:\n%s', json_dict)
        return json_dict
