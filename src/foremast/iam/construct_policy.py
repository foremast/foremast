"""Construct an IAM Policy from templates.

Examples:
    pipeline.json:

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

from ..utils import get_template, get_env_credential

LOG = logging.getLogger(__name__)


def construct_policy(app='coreforrest',
                     env='dev',
                     group='forrest',
                     region='us-east-1',
                     pipeline_settings=None):
    """Assemble IAM Policy for _app_.

    Args:
        app (str): Name of Spinnaker Application.
        pipeline_settings (dict): Settings from *pipeline.json*.

    Returns:
        str: Custom IAM Policy for _app_.
        None: When no *services* have been defined in *pipeline.json*.
    """
    LOG.info('Create custom IAM Policy for %s.', app)

    services = pipeline_settings.get('services', {})
    LOG.debug('Found requested services: %s', services)

    if services:
        credential = get_env_credential(env=env)
        account_number = credential['accountId']

    statements = []
    for service, value in services.items():
        if isinstance(value, (bool, str)):
            items = [value]
        else:
            items = value

        try:
            statement_block = get_template('iam/{0}.json.j2'.format(service),
                                           account_number=account_number,
                                           app=app,
                                           env=env,
                                           group=group,
                                           region=region,
                                           items=items)
            statement = json.loads(statement_block)
            statements.append(statement)
        except json.decoder.JSONDecodeError:
            statement_block_list = json.loads('[{0}]'.format(statement_block))
            statements.extend(statement_block_list)

    if statements:
        policy_json = get_template('iam/wrapper.json.j2',
                                   statements=json.dumps(statements))
    else:
        LOG.info('No services defined for %s.', app)
        policy_json = None

    return policy_json
