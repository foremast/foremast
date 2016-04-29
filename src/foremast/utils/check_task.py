"""Check Taskid status."""
import logging

import requests
from tryagain import retries

from ..consts import API_URL, HEADERS
from ..exceptions import SpinnakerTaskError

LOG = logging.getLogger(__name__)


@retries(max_attempts=10, wait=2, exceptions=(AssertionError, ValueError))
def check_task(taskid, app_name):
    """Check task status.

    Args:
        taskid: the task id returned from create_elb.
        app_name: application name related to this task.

    Returns:
        polls for task status.
    """
    try:
        taskurl = taskid.get('ref', '0000')
    except AttributeError:
        taskurl = taskid

    taskid = taskurl.split('/tasks/')[-1]

    LOG.info('Checking taskid %s', taskid)

    url = '{0}/applications/{1}/tasks/{2}'.format(API_URL, app_name, taskid)
    task_response = requests.get(url, headers=HEADERS)

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
