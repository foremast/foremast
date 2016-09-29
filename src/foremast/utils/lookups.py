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
