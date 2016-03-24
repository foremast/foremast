"""Create IAM Instance Profiles, Roles, Users, and Groups."""
import logging

import boto3
from boto3.exceptions import botocore

from .consts import ROLE_POLICY

LOG = logging.getLogger(__name__)


def create_iam_resources(env='dev', group='forrest', app='unicorn'):
    """Create the IAM Resources for the application.

    Args:
        env (str): Deployment environment, i.e. dev, stage, prod.
        group (str): Application Group name.
        app (str): Application name.

    Returns:
        True upon successful completion.
    """
    session = boto3.session.Session(profile_name=env)
    client = session.client('iam')

    user_name = '{group}_{app}'.format(group=group, app=app)
    role_name = '{user}_role'.format(user=user_name)
    profile_name = '{user}_profile'.format(user=user_name)

    resource_action(client,
                    action='create_role',
                    log_format='Role: %(RoleName)s',
                    RoleName=role_name,
                    AssumeRolePolicyDocument=ROLE_POLICY)
    resource_action(client,
                    action='create_instance_profile',
                    log_format='Instance Profile: %(InstanceProfileName)s',
                    InstanceProfileName=profile_name)
    attach_profile_to_role(client,
                           role_name=role_name,
                           profile_name=profile_name)

    resource_action(client,
                    action='create_user',
                    log_format='User: %(UserName)s',
                    UserName=user_name)
    resource_action(client,
                    action='create_group',
                    log_format='Group: %(GroupName)s',
                    GroupName=group)
    resource_action(client,
                    action='add_user_to_group',
                    log_format='User to Group: %(UserName)s -> %(GroupName)s',
                    log_failure=True,
                    GroupName=group,
                    UserName=user_name)

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
    current_instance_profiles = client.list_instance_profiles_for_role(
        RoleName=role_name)['InstanceProfiles']

    for profile in current_instance_profiles:
        if profile['InstanceProfileName'] == profile_name:
            LOG.info('Found Instance Profile attached to Role: %s -> %s',
                     profile_name, role_name)
            break
    else:
        for remove_profile in current_instance_profiles:
            client.remove_role_from_instance_profile(
                InstanceProfileName=remove_profile,
                RoleName=role_name)
            LOG.info('Removed Instance Profile from Role: %s -> %s',
                     remove_profile, role_name)

        client.add_role_to_instance_profile(InstanceProfileName=profile_name,
                                            RoleName=role_name)
        LOG.info('Added Instance Profile to Role: %s -> %s', profile_name,
                 role_name)

    return True


def resource_action(client,
                    action='',
                    log_format='item: %(key)s',
                    log_failure=False,
                    **kwargs):
    """Call _action_ using boto3 _client_ with _kwargs_.

    This is meant for _action_ methods that will create or implicitely prove a
    given Resource exists. The _log_failure_ flag is available for methods that
    should always succeed, but will occasionally fail due to unknown AWS
    issues.

    Args:
        client (botocore.client.IAM): boto3 client object.
        action (str): Client method to call.
        log_format (str): Generic log message format, 'Added' or 'Found' will
            be prepended depending on the scenario.
        log_failure (bool): Will log WARNING level 'Failed' instead of 'Found'
            message.
        **kwargs: Keyword arguments to pass to _action_ method.

    Returns:
        True upon successful completion.
    """
    try:
        getattr(client, action)(**kwargs)
        LOG.info(' '.join(('Added', log_format)), kwargs)
    except botocore.exceptions.ClientError:
        if not log_failure:
            LOG.info(' '.join(('Found', log_format)), kwargs)
        else:
            LOG.warning(' '.join(('Failed', log_format)), kwargs)

    return True
