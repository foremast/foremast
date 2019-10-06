#   Foremast - Pipeline Tooling
#
#   Copyright 2018 Gogo, LLC
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
"""Destroy Security Group Resources."""
import logging

from ...utils import get_template, get_vpc_id, wait_for_task
from ...utils.gate import gate_request

LOG = logging.getLogger(__name__)


def destroy_sg(app='', env='', region='', **_):
    """Destroy Security Group.

    Args:
        app (str): Spinnaker Application name.
        env (str): Deployment environment.
        region (str): Region name, e.g. us-east-1.

    Returns:
        True upon successful completion.
    """
    vpc = get_vpc_id(account=env, region=region)

    uri = '/securityGroups/{env}/{region}/{app}'.format(env=env, region=region, app=app)
    payload = {'vpcId': vpc}
    security_group = gate_request(uri=uri, params=payload)

    if not security_group:
        LOG.info('Nothing to delete.')
    else:
        LOG.info('Found Security Group in %(region)s: %(name)s', security_group)

        destroy_request = get_template('destroy/destroy_sg.json.j2', app=app, env=env, region=region, vpc=vpc)
        wait_for_task(destroy_request)

    return True
