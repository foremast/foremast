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

"""Destroy any ELB Resources."""

from ...utils import check_task, post_task, get_template, get_vpc_id


def destroy_elb(app='', env='dev', region='us-east-1', **_):
    """Destroy ELB Resources.

    Args:
        app (str): Spinnaker Application name.
        env (str): Deployment environment.
        region (str): AWS region.

    Returns:
        True upon successful completion.
    """
    task_json = get_template(
        template_file='destroy/destroy_elb.json.j2',
        app=app,
        env=env,
        region=region,
        vpc=get_vpc_id(account=env, region=region))

    task_id = post_task(task_json)
    check_task(task_id)

    return True
