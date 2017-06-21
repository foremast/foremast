"""Verify :func:`foremsat.utils.tasks.check_task` functionality."""
from unittest import mock

import pytest

from foremast.exceptions import SpinnakerTaskError
from foremast.utils.tasks import _check_task

FAIL_MESSAGE = 'TERMINAL'
SUCCESS_MESSAGE = 'SUCCEEDED'


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
