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
"""Construct an IAM Policy from templates.

Examples:
    pipeline.json::

        {
            "services": {
                "dynamodb": [
                    "another_app"
                ],
                "lambda": true,
                "s3": true
            }
        }
"""
import json
import logging

from ..utils import get_env_credential, get_template

LOG = logging.getLogger(__name__)


def auto_service(pipeline_settings={}, services={}):  # pylint: disable=W0102
    """Automatically enable service for deployment types.

    Args:
        services (dict): Services to enable in IAM Policy.
        pipeline_settings (dict): Settings from *pipeline.json*.

    Returns:
        dict: Services.
    """
    deployment_type = pipeline_settings['type']

    if deployment_type == 'lambda':
        services['lambda'] = True

    return services


def construct_policy(app='coreforrest', env='dev', group='forrest', region='us-east-1', pipeline_settings=None):
    """Assemble IAM Policy for _app_.

    Args:
        app (str): Name of Spinnaker Application.
        env (str): Environment/Account in AWS
        group (str):A Application group/namespace
        region (str): AWS region
        pipeline_settings (dict): Settings from *pipeline.json*.

    Returns:
        json: Custom IAM Policy for _app_.
        None: When no *services* have been defined in *pipeline.json*.
    """
    LOG.info('Create custom IAM Policy for %s.', app)

    services = pipeline_settings.get('services', {})
    LOG.debug('Found requested services: %s', services)

    services = auto_service(pipeline_settings=pipeline_settings, services=services)

    if services:
        credential = get_env_credential(env=env)
        account_number = credential['accountId']

    statements = []
    for service, value in services.items():
        if value is True:
            items = []
        elif isinstance(value, str):
            items = [value]
        else:
            items = value

        try:
            statement_block = get_template(
                'infrastructure/iam/{0}.json.j2'.format(service),
                account_number=account_number,
                app=app,
                env=env,
                group=group,
                region=region,
                items=items,
                settings=pipeline_settings)
            statement = json.loads(statement_block)
            statements.append(statement)
        except ValueError:
            LOG.debug('Need to make %s template into list.', service)
            statement_block_list = json.loads('[{0}]'.format(statement_block))
            statements.extend(statement_block_list)

    if statements:
        policy_json = get_template('infrastructure/iam/wrapper.json.j2', statements=json.dumps(statements))
    else:
        LOG.info('No services defined for %s.', app)
        policy_json = None

    return policy_json
