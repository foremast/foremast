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
    """
    LOG.info('Create custom IAM Policy for %s.', app)

    services = pipeline_settings['services']
    LOG.debug('Found requested services: %s', services)

    credential = get_env_credential(env=env)
    account_number = credential['accountId']

    statements = []
    for service, value in services.items():
        if isinstance(value, (bool, str)):
            items = [value]
        else:
            items = value

        statement = json.loads(get_template('iam/{0}.json.j2'.format(service),
                                            account_number=account_number,
                                            app=app,
                                            env=env,
                                            group=group,
                                            region=region,
                                            items=items))
        statements.append(statement)

    policy_json = get_template('iam/wrapper.json.j2',
                               statements=json.dumps(statements))

    return policy_json
