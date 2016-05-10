"""Create IAM Instance Profiles, Roles, Users, and Groups."""
import collections
import logging

import boto3

from ..utils import get_app_details, get_properties, get_template
from .construct_policy import construct_policy
from .resource_action import resource_action

LOG = logging.getLogger(__name__)


def create_iam_resources(env='dev', app='', **_):
    """Create the IAM Resources for the application.

    Args:
        env (str): Deployment environment, i.e. dev, stage, prod.
        app (str): Spinnaker Application name.

    Returns:
        True upon successful completion.
    """
    session = boto3.session.Session(profile_name=env)
    client = session.client('iam')

    generated = get_app_details.get_details(env=env, app=app)
    app_details = collections.namedtuple('AppDetails',
                                         ['group', 'policy', 'profile', 'role',
                                          'user'])
    details = app_details(**generated.iam())

    LOG.debug('Application details: %s', details)

    resource_action(
        client,
        action='create_role',
        log_format='Created Role: %(RoleName)s',
        RoleName=details.role,
        AssumeRolePolicyDocument=get_template('iam_role_policy.json'))
    resource_action(
        client,
        action='create_instance_profile',
        log_format='Created Instance Profile: %(InstanceProfileName)s',
        InstanceProfileName=details.profile)
    attach_profile_to_role(client,
                           role_name=details.role,
                           profile_name=details.profile)

    iam_policy = construct_policy(
        app=app,
        group=details.group,
        env=env,
        pipeline_settings=get_properties(env='pipeline'))
    if iam_policy:
        resource_action(client,
                        action='put_role_policy',
                        log_format='Added IAM Policy: %(PolicyName)s',
                        RoleName=details.role,
                        PolicyName=details.policy,
                        PolicyDocument=iam_policy)

    resource_action(client,
                    action='create_user',
                    log_format='Created User: %(UserName)s',
                    UserName=details.user)
    resource_action(client,
                    action='create_group',
                    log_format='Created Group: %(GroupName)s',
                    GroupName=details.group)
    resource_action(
        client,
        action='add_user_to_group',
        log_format='Added User to Group: %(UserName)s -> %(GroupName)s',
        GroupName=details.group,
        UserName=details.user)

    return True


def attach_profile_to_role(client,
                           role_name='forrest_unicorn_role',
                           profile_name='forrest_unicorn_profile'):
    """Attach an IAM Instance Profile _profile_name_ to Role _role_name_.

    Args:
        role_name (str): Name of Role.
        profile_name (str): Name of Instance Profile.

    Returns:
        True upon successful completion.
    """
    current_instance_profiles = resource_action(
        client,
        action='list_instance_profiles_for_role',
        log_format='Found Instance Profiles for %(RoleName)s.',
        RoleName=role_name)['InstanceProfiles']

    for profile in current_instance_profiles:
        if profile['InstanceProfileName'] == profile_name:
            LOG.info('Found Instance Profile attached to Role: %s -> %s',
                     profile_name, role_name)
            break
    else:
        for remove_profile in current_instance_profiles:
            resource_action(
                client,
                action='remove_role_from_instance_profile',
                log_format='Removed Instance Profile from Role: '
                '%(InstanceProfileName)s -> %(RoleName)s',
                InstanceProfileName=remove_profile['InstanceProfileName'],
                RoleName=role_name)

        resource_action(client,
                        action='add_role_to_instance_profile',
                        log_format='Added Instance Profile to Role: '
                        '%(InstanceProfileName)s -> %(RoleName)s',
                        InstanceProfileName=profile_name,
                        RoleName=role_name)

    return True
