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
"""Retrieve GCP Environments and their configuration"""

from src.foremast.consts import GCP_ENVS
from google.oauth2 import service_account


class GcpEnvironment:

    def __init__(self, name, **entries):
        self.name = name
        self.service_account_project = None
        self.service_account_path = None
        self.secret_manager_project = None
        self.__dict__.update(entries)

    def get_credentials(self):
        """Gets a GCP service account credentials"""
        credentials = service_account.Credentials.from_service_account_file(
            filename=self.service_account_path,
            scopes=['https://www.googleapis.com/auth/cloud-platform'])
        return credentials

    @staticmethod
    def get_environments_from_config():
        gcp_envs = dict()
        for env_name in GCP_ENVS:
            env_config = GCP_ENVS[env_name]
            gcp_envs[env_name] = GcpEnvironment(name=env_name, **env_config)
        return gcp_envs

