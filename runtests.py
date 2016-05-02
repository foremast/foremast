#!/usr/bin/env python3
"""Run tests for Pipes."""
import logging

import pytest

if __name__ == '__main__':
    """This is not the best way to run.

    Coverage report shows missing lines when in fact they are actually covered.
    This seems to be a known issue with py.test and something about import
    order. For now, run full command `py.test -v --cov pyasgard --cov-report
    term-missing --cov-report html test_pyasgard.py` or `tox`.
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(levelname)s]%(module)s:%(funcName)s - %(message)s')

    TEST_ARGS = ['-s', '-v', '--cov-report', 'term-missing', '--cov-report',
                 'html', '--cov', 'src/foremast', '--pep8', 'tests']

    pytest.main(TEST_ARGS)
