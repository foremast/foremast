import logging

import boto3

LOG = logging.getLogger(__name__)


def get_role_arn(role_name, env, region):
    """Gets role ARN given role name
    Args:
        role_name (str): Role name to lookup
        env (str): Environment in which to lookup
        region (str): Region

    Returns:
        ARN if role found
    """
    session = boto3.Session(profile_name=env, region_name=region)
    iam_client = session.client('iam')

    role = iam_client.get_role(RoleName=role_name)
    role_arn = role['Role']['Arn']

    LOG.debug("Found role's %s ARN %s", role_name, role_arn)

    return role_arn
