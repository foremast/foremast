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

"""Construct a block section of Stages in a Spinnaker Pipeline."""
import json
import logging
import os
import copy
from pprint import pformat

from ..utils import generate_encoded_user_data, get_template
from ..consts import ASG_WHITELIST

LOG = logging.getLogger(__name__)


def construct_pipeline_block(env='',
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
        template_name = 'pipeline/pipeline_{}.json.j2'.format(env)
    else:
        template_name = 'pipeline/pipeline_stages.json.j2'

    LOG.debug('%s info:\n%s', env, pformat(settings))

    gen_app_name = generated.app_name()
    user_data = generate_encoded_user_data(env=env,
                                           region=region,
                                           app_name=gen_app_name,
                                           group_name=generated.project)

    # Use different variable to keep template simple
    instance_security_groups = [
        'sg_apps',
        'sg_offices',
        gen_app_name,
    ]
    instance_security_groups.extend(
        settings['security_group']['instance_extras'])

    LOG.info('Instance security groups to attach: {0}'.format(instance_security_groups))

    # check if scaling policy exists
    if settings['asg']['scaling_policy']:
        scalingpolicy = True
        LOG.info('Found scaling policy')
    else:
        scalingpolicy = False
        LOG.info('No scaling policy found')

    if settings['app']['eureka_enabled']:
        elb = []
    else:
        elb = ['{0}'.format(gen_app_name)]
    LOG.info('Attaching the following ELB: {0}'.format(elb))

    provider_healthcheck = []
    for provider, active in settings['asg']['provider_healthcheck'].items():
        if active:
            provider_healthcheck.append(provider.capitalize())
    LOG.info('Provider healthchecks: {0}'.format(provider_healthcheck))

    has_provider_healthcheck = False
    if len(provider_healthcheck) > 0:
        has_provider_healthcheck = True

    data = copy.deepcopy(settings)

    # Default HC type in DEV to EC2, default to EC2 if eureka enabled
    if env == 'dev' or settings['app']['eureka_enabled']:
        data['asg'].update({
            'hc_type': 'EC2'
        })
        LOG.info('Switching health check type to: EC2')

    LOG.info('White listed dev asg apps: {0}'.format(ASG_WHITELIST))
    if env == 'dev' and gen_app_name not in ASG_WHITELIST:
        data['asg'].update({
            'max_inst': '1',
            'min_inst': '1'
        })
        LOG.info('App {0} is not white listed, using default dev ASG settings'.format(gen_app_name))

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
        'elb': json.dumps(elb),
        'promote_restrict': pipeline_data['promote_restrict'],
        'owner_email': pipeline_data['owner_email'],
        'scalingpolicy': scalingpolicy
    })

    data['asg'].update({
        'hc_type': data['asg'].get('hc_type').upper(),
        'provider_healthcheck': json.dumps(provider_healthcheck),
        "has_provider_healthcheck": has_provider_healthcheck,
    })

    LOG.debug('Block data:\n%s', pformat(data))

    pipeline_json = get_template(template_file=template_name, data=data)
    return pipeline_json
