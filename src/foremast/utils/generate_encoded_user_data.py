import base64
from ..utils import get_template


def generate_encoded_user_data(env='dev',
                               region='us-east-1',
                               app_name='',
                               group_name=''):
    r"""Generate base64 encoded User Data.

    Args:
        env (str): Deployment environment, e.g. dev, stage.
        region (str): AWS Region, e.g. us-east-1.
        app_name (str): Application name, e.g. coreforrest.
        group_name (str): Application group nane, e.g. core.

    Returns:
        str: base64 encoded User Data script.

            #!/bin/bash
            export CLOUD_ENVIRONMENT=dev
            export CLOUD_APP=coreforrest
            export CLOUD_APP_GROUP=forrest
            export CLOUD_STACK=forrest
            export EC2_REGION=us-east-1
            export CLOUD_DOMAIN=dev.example.com
            printenv | grep 'CLOUD\|EC2' | awk '$0="export "$0'>> /etc/gogo/cloud_env
    """
    user_data = get_template(template_file='user_data.sh.j2',
                             env=env,
                             region=region,
                             app_name=app_name,
                             group_name=group_name, )
    return base64.b64encode(user_data.encode()).decode()
