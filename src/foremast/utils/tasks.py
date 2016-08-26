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

"""POST a new task or check status of running task"""
import logging

import json
import requests
from tryagain import retries

from ..consts import API_URL, HEADERS, GATE_CLIENT_CERT, GATE_CA_BUNDLE
from ..exceptions import SpinnakerTaskError

LOG = logging.getLogger(__name__)


def post_task(task_data):
    """POST JSON to Spinnaker /tasks.

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

    resp = requests.post(url,
                         data=task_json,
                         headers=HEADERS,
                         verify=GATE_CA_BUNDLE,
                         cert=GATE_CLIENT_CERT)
    resp_json = resp.json()

    LOG.debug(resp_json)

    assert resp.ok, 'Spinnaker communication error: {0}'.format(
        resp.text)

    return resp_json['ref']


@retries(max_attempts=50, wait=2, exceptions=(AssertionError, ValueError))
def check_task(taskid):
    """Check task status.

    Args:
        taskid (str): the task id returned from create_elb.

    Returns:
        polls for task status.
    """
    try:
        taskurl = taskid.get('ref', '0000')
    except AttributeError:
        taskurl = taskid

    taskid = taskurl.split('/tasks/')[-1]

    LOG.info('Checking taskid %s', taskid)

    url = '{}/tasks/{}'.format(API_URL, taskid)
    task_response = requests.get(url,
                                 headers=HEADERS,
                                 verify=GATE_CA_BUNDLE,
                                 cert=GATE_CLIENT_CERT)

    LOG.debug(task_response.json())

    assert task_response.ok, 'Spinnaker communication error: {0}'.format(
        task_response.text)

    task_state = task_response.json()
    status = task_state['status']
    LOG.info('Current task status: %s', status)

    if status == 'SUCCEEDED':
        return status
    elif status == 'TERMINAL':
        raise SpinnakerTaskError(task_state)
    else:
        raise ValueError
