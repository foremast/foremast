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
"""Create GCP Service Account"""

import os
import logging

from google.oauth2 import service_account
import googleapiclient.discovery

LOG = logging.getLogger(__name__)


def create_service_account(project, service_account_name):
    """Creates a GCP Service account if it does not already exists"""

    credentials = service_account.Credentials.from_service_account_file(
        filename=os.environ['GOOGLE_APPLICATION_CREDENTIALS'],
        scopes=['https://www.googleapis.com/auth/cloud-platform'])

    service = googleapiclient.discovery.build(
        'iam', 'v1', credentials=credentials)

    app_service_account = service.projects().serviceAccounts().create(
        name='projects/' + project,
        body={
            'accountId': service_account_name,
            'serviceAccount': {
                'displayName': service_account_name
            }
        }).execute()

    LOG.info('Created service account: ' + app_service_account['email'])

    return app_service_account
