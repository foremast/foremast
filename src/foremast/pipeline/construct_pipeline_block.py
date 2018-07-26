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
import collections
import copy
import json
import logging
from pprint import pformat

from ..consts import ASG_WHITELIST, DEFAULT_EC2_SECURITYGROUPS, EC2_PIPELINE_TYPES
from ..utils import generate_encoded_user_data, get_template, remove_duplicate_sg

LOG = logging.getLogger(__name__)


def check_provider_healthcheck(settings, default_provider='Discovery'):
    """Set Provider Health Check when specified.

    Returns:
        collections.namedtuple: **ProviderHealthCheck** with attributes:

            * providers (list): Providers set to use native Health Check.
            * has_healthcheck (bool): If any native Health Checks requested.
    """
    # pylint: disable=invalid-name
    ProviderHealthCheck = collections.namedtuple('ProviderHealthCheck', ['providers', 'has_healthcheck'])

    eureka_enabled = settings['app']['eureka_enabled']
    providers = settings['asg']['provider_healthcheck']

    LOG.debug('Template defined Health Check Providers: %s', providers)

    health_check_providers = []
    has_healthcheck = False

    normalized_default_provider = default_provider.capitalize()

    if eureka_enabled:
        LOG.info('Eureka enabled, enabling default Provider Health Check: %s', normalized_default_provider)

        for provider, active in providers.items():
            if provider.lower() == normalized_default_provider.lower():
                providers[provider] = True
                LOG.debug('Override defined Provider Health Check: %s -> %s', active, providers[provider])
                break
        else:
            LOG.debug('Adding default Provider Health Check: %s', normalized_default_provider)
            providers[normalized_default_provider] = True

    for provider, active in providers.items():
        if active:
            health_check_providers.append(provider.capitalize())
    LOG.info('Provider healthchecks: %s', health_check_providers)

    if health_check_providers:
        has_healthcheck = True

    return ProviderHealthCheck(providers=health_check_providers, has_healthcheck=has_healthcheck)


def get_template_name(env, pipeline_type):
    """Generates the correct template name based on pipeline type

    Args:
        env (str): environment to generate templates for
        pipeline_type (str): Type of pipeline like ec2 or lambda

    Returns:
        str: Name of template
    """
    pipeline_base = 'pipeline/pipeline'
    template_name_format = '{pipeline_base}'
    if env.startswith('prod'):
        template_name_format = template_name_format + '_{env}'
    else:
        template_name_format = template_name_format + '_stages'

    if pipeline_type != 'ec2':
        template_name_format = template_name_format + '_{pipeline_type}'

    template_name_format = template_name_format + '.json.j2'
    template_name = template_name_format.format(pipeline_base=pipeline_base, env=env, pipeline_type=pipeline_type)

    return template_name


def construct_pipeline_block(env='',
                             generated=None,
                             previous_env='',
                             region='us-east-1',
                             settings=None,
                             pipeline_data=None,
                             region_subnets=None):
    """Create the Pipeline JSON from template.

    This handles the common repeatable patterns in a pipeline, such as
    judgement, infrastructure, tagger and qe.

    Note:
       ASG Health Check type is overridden to `EC2` when deploying to **dev** or
       using :ref:`eureka_enabled`.

    Args:
        env (str): Deploy environment name, e.g. dev, stage, prod.
        generated (gogoutils.Generator): Gogo Application name generator.
        previous_env (str): The previous deploy environment to use as
            Trigger.
        region (str): AWS Region to deploy to.
        settings (dict): Environment settings from configurations.
        pipeline_data (dict): Pipeline settings from configurations
        region_subnets (dict): Subnets for a Region, e.g.
            {'us-west-2': ['us-west-2a', 'us-west-2b', 'us-west-2c']}.

    Returns:
        dict: Pipeline JSON template rendered with configurations.

    """

    LOG.info('%s block for [%s].', env, region)
    LOG.debug('%s info:\n%s', env, pformat(settings))

    pipeline_type = pipeline_data['type']

    if pipeline_type in EC2_PIPELINE_TYPES:
        data = ec2_pipeline_setup(
            generated=generated,
            settings=settings,
            env=env,
            region=region,
            project=generated.project,
            region_subnets=region_subnets,
        )
    else:
        data = copy.deepcopy(settings)

    data['app'].update({
        'appname': generated.app_name(),
        'repo_name': generated.repo,
        'group_name': generated.project,
        'environment': env,
        'region': region,
        'previous_env': previous_env,
        'promote_restrict': pipeline_data['promote_restrict'],
        'owner_email': pipeline_data['owner_email'],
        'pipeline': pipeline_data,
    })

    LOG.debug('Block data:\n%s', pformat(data))

    template_name = get_template_name(env, pipeline_type)
    pipeline_json = get_template(template_file=template_name, data=data, formats=generated)
    return pipeline_json


def ec2_pipeline_setup(generated=None, project='', settings=None, env='', region='', region_subnets=None):
    """Handles ec2 pipeline data setup

    Args:
        generated (gogoutils.Generator): Generated naming formats.
        project (str): Group name of application
        settings (dict): Environment settings from configurations.
        env (str): Deploy environment name, e.g. dev, stage, prod.
        region (str): AWS Region to deploy to.
        region_subnets (dict): Subnets for a Region, e.g.
            {'us-west-2': ['us-west-2a', 'us-west-2b', 'us-west-2c']}.

    Returns:
        dict: Updated settings to pass to templates for EC2 info

    """
    data = copy.deepcopy(settings)
    user_data = generate_encoded_user_data(
        env=env,
        region=region,
        generated=generated,
        group_name=project,
    )

    # Use different variable to keep template simple
    instance_security_groups = sorted(DEFAULT_EC2_SECURITYGROUPS[env])
    instance_security_groups.append(generated.security_group_app)
    instance_security_groups.extend(settings['security_group']['instance_extras'])
    instance_security_groups = remove_duplicate_sg(instance_security_groups)

    LOG.info('Instance security groups to attach: %s', instance_security_groups)

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
        elb = [generated.elb_app]
    LOG.info('Attaching the following ELB: %s', elb)

    health_checks = check_provider_healthcheck(settings)

    # Use EC2 Health Check for DEV or Eureka enabled
    if env == 'dev' or settings['app']['eureka_enabled']:
        data['asg'].update({'hc_type': 'EC2'})
        LOG.info('Switching health check type to: EC2')

    # Aggregate the default grace period, plus the exposed app_grace_period
    # to allow per repo extension of asg healthcheck grace period
    hc_grace_period = data['asg'].get('hc_grace_period')
    app_grace_period = data['asg'].get('app_grace_period')
    grace_period = hc_grace_period + app_grace_period

    # TODO: Migrate the naming logic to an external library to make it easier
    #       to update in the future. Gogo-Utils looks like a good candidate
    ssh_keypair = data['asg'].get('ssh_keypair', None)
    if not ssh_keypair:
        ssh_keypair = '{0}_{1}_default'.format(env, region)
    LOG.info('SSH keypair (%s) used', ssh_keypair)

    if settings['app']['canary']:
        canary_user_data = generate_encoded_user_data(
            env=env,
            region=region,
            generated=generated,
            group_name=project,
            canary=True,
        )
        data['app'].update({
            'canary_encoded_user_data': canary_user_data,
        })

    data['asg'].update({
        'hc_type': data['asg'].get('hc_type').upper(),
        'hc_grace_period': grace_period,
        'ssh_keypair': ssh_keypair,
        'provider_healthcheck': json.dumps(health_checks.providers),
        'enable_public_ips': json.dumps(settings['asg']['enable_public_ips']),
        'has_provider_healthcheck': health_checks.has_healthcheck,
        'asg_whitelist': ASG_WHITELIST,
    })

    data['app'].update({
        'az_dict': json.dumps(region_subnets),
        'encoded_user_data': user_data,
        'instance_security_groups': json.dumps(instance_security_groups),
        'elb': json.dumps(elb),
        'scalingpolicy': scalingpolicy,
    })

    return data
