"""Post JSON to tasks"""
import logging

import json
import requests

from ..consts import API_URL, HEADERS
from ..exceptions import SpinnakerTaskError

LOG = logging.getLogger(__name__)

def post_task(task_data):
    """Posts JSON to /tasks.

    Args:
        task_data (str): the task json that needs posted.

    Returns:
        str: taskid.
    """

    url = '{}/tasks'.format(API_URL)

    if isinstance(task_data, str):
        task_json = task_data
    else:
        task_json = json.dumps(task_data)

    r = requests.post(url, data=task_json, headers=HEADERS)

    LOG.debug(r.json())

    assert r.ok, 'Spinnaker communication error: {0}'.format(
        r.text)

    return r.json()['ref']

