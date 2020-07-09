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
"""Package for managing IAM in GCP. Spinnaker does not
directly interface with IAM so this package mostly uses Google's cloud packages
"""

import logging
from .service_account import create_service_account, list_service_accounts
from .policy import get_policy, set_policy, modify_policy_remove_member, modify_policy_add_binding
from .create_iam_resources import create_iam_resources

LOG = logging.getLogger(__name__)
