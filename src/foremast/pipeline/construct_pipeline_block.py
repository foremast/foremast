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
import collections
import copy
import json
import logging
from pprint import pformat

from ..consts import ASG_WHITELIST, DEFAULT_EC2_SECURITYGROUPS
from ..utils import generate_encoded_user_data, get_template

LOG = logging.getLogger(__name__)


def check_provider_healthcheck(settings, default_provider='Discovery'):
    """Set Provider Health Check when specified.

    Returns:
        collections.namedtuple: **ProviderHealthCheck** with attributes:

            * providers (list): Providers set to use native Health Check.
            * has_healthcheck (bool): If any native Health Checks requested.
    """
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

    if len(health_check_providers) > 0:
        has_healthcheck = True

    return ProviderHealthCheck(providers=health_check_providers, has_healthcheck=has_healthcheck)


def construct_pipeline_block(pipeline_type='ec2',
                             env='',
                             generated=None,
                             previous_env=None,
                             region='us-east-1',
                             settings=None,
                             pipeline_data=None,
                             **kwargs):
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
        region_subnets (dict): Subnets for a Region, e.g.
            {'us-west-2': ['us-west-2a', 'us-west-2b', 'us-west-2c']}.

    Returns:
        dict: Pipeline JSON template rendered with configurations.

    """
    LOG.info('%s block for [%s].', env, region)

    if pipeline_type == 'ec2':
        if env.startswith('prod'):
            template_name = 'pipeline/pipeline_{}.json.j2'.format(env)
        else:
            template_name = 'pipeline/pipeline_stages.json.j2'
    else:
        if env.startswith('prod'):
            template_name = 'pipeline/pipeline_{}_{}.json.j2'.format(env, pipeline_type)
        else:
            template_name = 'pipeline/pipeline_stages_{}.json.j2'.format(pipeline_type)

    LOG.debug('%s info:\n%s', env, pformat(settings))

    gen_app_name = generated.app_name()
    data = copy.deepcopy(settings)

    setup_kwargs = {
        'appname': gen_app_name,
        'settings': settings,
        'env': env,
        'region': region,
        'project': generated.project
    }
    if pipeline_type == 'ec2':
        setup_kwargs['region_subnets'] = kwargs['region_subnets']
        data = ec2_pipeline_setup(**setup_kwargs)
    elif pipeline_type == 'lambda':
        setup_kwargs['region_subnets'] = kwargs['region_subnets']
        data = lambda_pipeline_setup(**setup_kwargs)

    data['app'].update({
        'appname': gen_app_name,
        'repo_name': generated.repo,
        'group_name': generated.project,
        'environment': env,
        'region': region,
        'previous_env': previous_env,
        'promote_restrict': pipeline_data['promote_restrict'],
        'owner_email': pipeline_data['owner_email'],
    })

    LOG.debug('Block data:\n%s', pformat(data))

    pipeline_json = get_template(template_file=template_name, data=data)
    return pipeline_json


def lambda_pipeline_setup(**kwargs):
    """Handles lambda pipeline data setup
    
    Returns:
        dict: Updated settings to pass to templates for lambda info
    """

    settings = kwargs['settings']
    appname = kwargs['appname']
    env = kwargs['env']
    region = kwargs['region']
    project = kwargs['project']
    data = copy.deepcopy(settings)

    # Use different variable to keep template simple
    instance_security_groups = list(DEFAULT_EC2_SECURITYGROUPS)
    instance_security_groups.append(appname)
    instance_security_groups.extend(settings['security_group']['instance_extras'])

    LOG.info('Instance security groups to attach: {0}'.format(instance_security_groups))

    data = copy.deepcopy(settings)

    data['app'].update({
        'az_dict': json.dumps(kwargs['region_subnets']),
        'instance_security_groups': json.dumps(instance_security_groups),
        'function_name': pipeline_data['lambda']['handler']
    })

    return data


def ec2_pipeline_setup(**kwargs):
    """Handles ec2 pipeline data setup
    
    Returns:
        dict: Updated settings to pass to templates for EC2 info
    """

    settings = kwargs['settings']
    appname = kwargs['appname']
    env = kwargs['env']
    region = kwargs['region']
    project = kwargs['project']
    data = copy.deepcopy(settings)

    user_data = generate_encoded_user_data(env=env, region=region, app_name=appname, group_name=project)

    # Use different variable to keep template simple
    instance_security_groups = list(DEFAULT_EC2_SECURITYGROUPS)
    instance_security_groups.append(appname)
    instance_security_groups.extend(settings['security_group']['instance_extras'])

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
        elb = ['{0}'.format(appname)]
    LOG.info('Attaching the following ELB: {0}'.format(elb))

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
    LOG.info('SSH keypair ({0}) used'.format(ssh_keypair))
    if not ssh_keypair:
        ssh_keypair = '{0}_{1}_default'.format(env, region)
    LOG.info('SSH keypair ({0}) used'.format(ssh_keypair))

    if settings['app']['canary']:
        canary_user_data = generate_encoded_user_data(
            env=env, region=region, app_name=appname, group_name=project, canary=True)
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
        'az_dict': json.dumps(kwargs['region_subnets']),
        'encoded_user_data': user_data,
        'instance_security_groups': json.dumps(instance_security_groups),
        'elb': json.dumps(elb),
        'scalingpolicy': scalingpolicy,
    })

    return data


def ec2_bake_data(settings=None, base=None, region='us-east-1', provider='aws'):
    """Sets up extra data for EC2 wrapper/baking stage"""

    baking_process = settings['pipeline']['image']['builder']
    root_volume_size = settings['pipeline']['image']['root_volume_size']
    if root_volume_size > 50:
        raise SpinnakerPipelineCreationFailed(
            'Setting "root_volume_size" over 50G is not allowed. We found {0}G in your configs.'.format(
                root_volume_size))
    ami_id = ami_lookup(name=base, region=region)
    ami_template_file = generate_packer_filename(provider, region, baking_process)
    bake_data = {'ami_id': ami_id, 'root_volume_size': root_volume_size, 'ami_template_file': ami_template_file}
    return bake_data
