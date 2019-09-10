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
"""Construct a block section of Stages in a Spinnaker Pipeline."""
import copy
import json
import logging
from pprint import pformat

from ..consts import DEFAULT_EC2_SECURITYGROUPS
from ..utils import generate_encoded_user_data, get_template, remove_duplicate_sg

LOG = logging.getLogger(__name__)


def construct_pipeline_block_lambda(env='',
                                    generated=None,
                                    previous_env=None,
                                    region='us-east-1',
                                    region_subnets=None,
                                    settings=None,
                                    pipeline_data=None):
    """Create the Pipeline JSON from template.

    This handles the common repeatable patterns in a pipeline, such as
    judgement, infrastructure, tagger and qe.

    Args:
        env (str): Deploy environment name, e.g. dev, stage, prod.
        generated (gogoutils.Generator): Gogo Application name generator.
        previous_env (str): The previous deploy environment to use as
            Trigger.
        region (str): AWS Region to deploy to.
        settings (dict): Environment settings from configurations.
        region_subnets (dict): Subnets for a Region, e.g.
            {'us-west-2': ['us-west-2a', 'us-west-2b', 'us-west-2c']}.

    Returns:
        dict: Pipeline JSON template rendered with configurations.

    """
    LOG.info('%s block for [%s].', env, region)

    if env.startswith('prod'):
        template_name = 'pipeline/pipeline_{}_lambda.json.j2'.format(env)
    else:
        template_name = 'pipeline/pipeline_stages_lambda.json.j2'

    LOG.debug('%s info:\n%s', env, pformat(settings))

    gen_app_name = generated.app_name()
    user_data = generate_encoded_user_data(
        env=env,
        region=region,
        generated=generated,
        group_name=generated.project,
    )

    # Use different variable to keep template simple
    instance_security_groups = sorted(DEFAULT_EC2_SECURITYGROUPS[env])
    instance_security_groups.append(gen_app_name)
    instance_security_groups.extend(settings['security_group']['instance_extras'])
    instance_security_groups = remove_duplicate_sg(instance_security_groups)

    LOG.info('Instance security groups to attach: %s', instance_security_groups)

    data = copy.deepcopy(settings)

    data['app'].update({
        'appname': gen_app_name,
        'repo_name': generated.repo,
        'group_name': generated.project,
        'environment': env,
        'region': region,
        'az_dict': json.dumps(region_subnets),
        'previous_env': previous_env,
        'encoded_user_data': user_data,
        'instance_security_groups': json.dumps(instance_security_groups),
        'promote_restrict': pipeline_data['promote_restrict'],
        'owner_email': pipeline_data['owner_email'],
        'function_name': pipeline_data['lambda']['handler']
    })

    LOG.debug('Block data:\n%s', pformat(data))

    pipeline_json = get_template(template_file=template_name, data=data, formats=generated)
    return pipeline_json
