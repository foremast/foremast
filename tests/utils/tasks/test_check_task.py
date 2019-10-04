"""Verify :func:`foremsat.utils.tasks.check_task` functionality."""
from unittest import mock

import pytest

from foremast.exceptions import SpinnakerTaskError, SpinnakerTaskInconclusiveError
from foremast.utils.tasks import _check_task, check_task

FAIL_MESSAGE = 'TERMINAL'
SUCCESS_MESSAGE = 'SUCCEEDED'


@mock.patch('foremast.utils.tasks._check_task')
def test_utils_retry_task(mock_check_task):
    """Validate task retries are configurable."""
    taskid = 'fake_task'
    mock_check_task.side_effect = ValueError
    with pytest.raises(SpinnakerTaskInconclusiveError):
        check_task(taskid, timeout=2, wait=1)
    assert mock_check_task.call_count == 2


@mock.patch('foremast.utils.tasks.gate_request')
def test_task_success(mock_gate_request):
    """Successful Task."""
    mock_gate_request.return_value.json.return_value = {'status': SUCCESS_MESSAGE}

    result = _check_task(taskid='')

    assert result == SUCCESS_MESSAGE


@mock.patch('foremast.utils.tasks.gate_request')
def test_task_failure(mock_gate_request):
    """Failed Task."""
    mock_gate_request.return_value.json.return_value = {
        'status': FAIL_MESSAGE,
        'execution': {
            'stages': [],
        },
    }

    with pytest.raises(SpinnakerTaskError):
        _check_task(taskid='')


@mock.patch('foremast.utils.tasks.gate_request')
def test_task_unknown(mock_gate_request):
    """Unknown Task status raises exception to keep polling."""
    mock_gate_request.get.return_value.json.return_value = {'status': ''}

    with pytest.raises(ValueError):
        _check_task(taskid='')
