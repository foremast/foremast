"""Verify :func:`foremsat.utils.tasks.check_task` functionality."""
from unittest import mock

import pytest

from foremast.exceptions import SpinnakerTaskError, SpinnakerTaskInconclusiveError
from foremast.utils.tasks import _check_task, check_task

FAIL_MESSAGE = 'TERMINAL'
SUCCESS_MESSAGE = 'SUCCEEDED'


@mock.patch('foremast.utils.tasks._check_task')
@mock.patch('foremast.utils.tasks.requests.get')
def test_utils_retry_task(mock_requests_get, mock_check_task):
    """Validate task retries are configurable"""
    taskid = 'fake_task'
    mock_check_task.side_effect = ValueError
    with pytest.raises(SpinnakerTaskInconclusiveError):
        check_task(taskid, timeout=2, wait=1)
    assert mock_check_task.call_count == 2


@mock.patch('foremast.utils.tasks.requests')
def test_task_success(mock_requests):
    """Successful Task."""
    mock_requests.get.return_value.json.return_value = {'status': SUCCESS_MESSAGE}

    result = _check_task(taskid='')

    assert result == SUCCESS_MESSAGE


@mock.patch('foremast.utils.tasks.requests')
def test_task_failure(mock_requests):
    """Failed Task."""
    mock_requests.get.return_value.json.return_value = {
        'status': FAIL_MESSAGE,
        'execution': {
            'stages': [],
        },
    }

    with pytest.raises(SpinnakerTaskError):
        _check_task(taskid='')


@mock.patch('foremast.utils.tasks.requests')
def test_task_unknown(mock_requests):
    """Unknown Task status raises exception to keep polling."""
    mock_requests.get.return_value.json.return_value = {'status': ''}

    with pytest.raises(ValueError):
        _check_task(taskid='')


@mock.patch('foremast.utils.tasks._check_task')
def test_polling_inconclusive(mock_check):
    """Spinnaker Task with non-terminal state should raise exception."""
    mock_check.side_effect = ValueError

    with pytest.raises(SpinnakerTaskInconclusiveError):
        check_task(taskid='', timeout=1, wait=1)
