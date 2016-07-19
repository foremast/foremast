"""Lookup AMI ID from a simple name."""
import json
import logging
import os
from base64 import b64decode

import gitlab
import requests

from ..consts import GIT_URL, GITLAB_TOKEN, AMI_BASE_URL

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

    if AMI_BASE_URL is not None:
        full_ami_url = "{}/ami-xxxx{}.json".format(AMI_BASE_URL, region)
        LOG.info("Getting AMI from %s" % full_ami_url)
        response = requests.get(full_ami_url)
        assert response.ok, "Error getting ami info from {}".format(
                full_ami_url)

        ami_dict = response.json()
        ami_id = ami_dict[region][name]
    else if GITLAB_TOKEN is not None:
        LOG.info("Getting AMI from Gitlab")
        server = gitlab.Gitlab(GIT_URL, token=GITLAB_TOKEN)
        project_id = server.getproject('devops/ansible')['id']

        ami_blob = server.getfile(project_id, 'scripts/{0}.json'.format(region),
                                  'master')
        ami_contents = b64decode(ami_blob['content']).decode()
        ami_dict = json.loads(ami_contents)
        ami_id = ami_dict[name]
    else:
        ami_id = name

    LOG.debug('AMI table: %s', ami_dict)

    return ami_id
