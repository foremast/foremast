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
"""GCP Service Account helpers"""

import logging

import googleapiclient.discovery

LOG = logging.getLogger(__name__)


def create_service_account(credentials, project_id, name):
    """Creates a service account."""

    service_accounts = list_service_accounts(credentials, project_id)

    # Check if the SA already exists
    for account in service_accounts['accounts']:
        if name == account['displayName']:
            LOG.info("GCP service account %s already exists", name)
            return account

    LOG.info("GCP service account %s does not exist", name)

    service = googleapiclient.discovery.build(
        'iam', 'v1', credentials=credentials, cache_discovery=False)

    app_svc_account = service.projects().serviceAccounts().create(
        name='projects/' + project_id,
        body={
            'accountId': name,
            'serviceAccount': {
                'displayName': name,
                'description': 'Managed by Foremast'
            }
        }).execute()

    LOG.info("Created GCP service account with email %s", app_svc_account['email'])
    return app_svc_account


def list_service_accounts(credentials, project_id):
    """Lists all service accounts for the given project."""

    service = googleapiclient.discovery.build(
        'iam', 'v1', credentials=credentials, cache_discovery=False)

    service_accounts = service.projects().serviceAccounts().list(
        name='projects/' + project_id).execute()

    return service_accounts
