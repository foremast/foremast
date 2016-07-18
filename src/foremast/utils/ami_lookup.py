"""Lookup AMI ID from a simple name."""
import json
import logging
import os
from base64 import b64decode

import gitlab

from ..consts import GIT_URL, GITLAB_TOKEN

LOG = logging.getLogger(__name__)


def ami_lookup(region='us-east-1', name='tomcat8'):
    """Use _name_ to find AMI ID.

    Args:
        region (str): AWS Region to find AMI ID.
        name (str): Simple AMI base name to lookup.

    Returns:
        str: AMI ID for _name_ in _region_.
    """

    server = gitlab.Gitlab(GIT_URL, token=GITLAB_TOKEN)
    project_id = server.getproject('devops/ansible')['id']

    ami_blob = server.getfile(project_id, 'scripts/{0}.json'.format(region),
                              'master')
    ami_contents = b64decode(ami_blob['content']).decode()
    LOG.debug('AMI table: %s', ami_contents)

    ami_dict = json.loads(ami_contents)

    return ami_dict[name]

print(ami_lookup())
