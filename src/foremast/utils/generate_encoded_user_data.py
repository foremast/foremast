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

"""Generate base64 encoded User Data."""
import base64

from .templates import get_template


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
            export CLOUD_ENVIRONMENT_C=dev
            export CLOUD_ENVIRONMENT_P=dev
            export CLOUD_ENVIRONMENT_S=dev
            export CLOUD_APP=coreforrest
            export CLOUD_APP_GROUP=forrest
            export CLOUD_STACK=forrest
            export EC2_REGION=us-east-1
            export CLOUD_DOMAIN=dev.example.com
            printenv | grep 'CLOUD\|EC2' | awk '$0="export "$0'>> /etc/gogo/cloud_env
    """
    # We need to handle the case of prodp and prods for different URL generation
    if env in ["prod", "prodp", "prods"]:
        env_c, env_p, env_s = "prod", "prodp", "prods"
    else:
        env_c, env_p, env_s = env, env, env
    user_data = get_template(template_file='infrastructure/user_data.sh.j2',
                             env=env,
                             env_c=env_c,
                             env_p=env_p,
                             env_s=env_s,
                             region=region,
                             app_name=app_name,
                             group_name=group_name, )
    return base64.b64encode(user_data.encode()).decode()
