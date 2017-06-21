#   Foremast - Pipeline Tooling
#
#   Copyright 2016 Gogo, LLC #
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
from functools import partial
import json
import logging

import requests
from tryagain import call as retry_call 

from ..consts import API_URL, GATE_CA_BUNDLE, GATE_CLIENT_CERT, HEADERS, DEFAULT_TASK_TIMEOUT, TASK_TIMEOUTS
from ..exceptions import SpinnakerTaskError, SpinnakerTaskInconclusiveError

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


def _check_task(taskid):
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


def check_task(taskid, timeout=DEFAULT_TASK_TIMEOUT, wait=2):
    """wrapper for check_task

    Args:
        taskid (str): the task id returned from post_task 
        timeout (int) (optional): how long to wait before failing the task
        wait (int, optional): Seconds to pause between polling attempts.

    Returns:
        polls for task status.

    Raises:
        AssertionError: API did not responde with a 200 status code.
        foremast.exceptions.SpinnakerTaskInconclusiveError: Task did not reach a
            terminal state in the given time.

    """
    max_attempts = int(timeout / wait)
    try:
        return retry_call(
            partial(_check_task, taskid),
            max_attempts=max_attempts,
            wait=wait,
            exceptions=(AssertionError, ValueError), )
    except ValueError:
        raise SpinnakerTaskInconclusiveError('Task failed to complete in {0} seconds: {1}'.format(timeout, taskid))


def wait_for_task(task_data):
    """Run task and check the result

    Args:
        task_data (str): the task json to execute 

    Returns:
        polls for task status
    """
    taskid = post_task(task_data)

    if isinstance(task_data, str):
        json_data = json.loads(task_data) 
    else:
        json_data = task_data

    # inspect the task to see if a timeout is configured
    job = json_data['job'][0]
    env = job.get('credentials')
    task_type = job.get('type')

    timeout = TASK_TIMEOUTS.get(env, dict()).get(task_type, DEFAULT_TASK_TIMEOUT)

    LOG.debug("Task %s will timeout after %s", task_type, timeout)

    check_task(taskid, timeout)
