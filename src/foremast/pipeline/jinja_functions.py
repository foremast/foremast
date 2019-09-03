#   Foremast - Pipeline Tooling
#
#   Copyright 2019 Gogo, LLC
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
"""Functions that can be exposed to Jinja2 templates"""

from ..utils import get_canary_id


def get_jinja_functions():
    """Gets a dictionary of functions that can be exposed to Jinja templates"""
    functions = dict()
    functions[get_canary_id.__name__] = get_canary_id

    return functions
