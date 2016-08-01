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
