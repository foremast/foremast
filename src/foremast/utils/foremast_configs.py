#   Foremast - Pipeline Tooling
#
#   Copyright 2020 Redbox Automated Retail, LLC
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
"""Set of utility functions for Foremasts configs"""


def verify_approval_skip(data, env, env_configs):
    """Determines if a approval stage can be added/removed from a given
    environment pipeline stage based on environment setting. Defaults to false,
    and verifies administrators allow skips in given environments.
    Args:
        data (dict): environment config data from pipeline files
        env (str): Name of environment
        env_configs (dict): environment configs from foremast files

    Returns:
        bool: result of approval skip check/verification and setting
    """

    approval_skip = False

    if 'approval_skip' in data['app']:
        if env in env_configs and env_configs[env]['enable_approval_skip']:
            approval_skip = data['app']['approval_skip']

    return approval_skip
