"""Archaius functions for deployment."""
import logging

import boto3

from .utils import get_details

LOG = logging.getLogger(__name__)


def init_properties(env='dev', app='unnecessary'):
    """Make sure _application.properties_ file exists in S3.

    For Applications with Archaius support, there needs to be a file where the
    cloud environment variable points to.

    Args:
        env (str): Deployment environment, i.e. dev, stage, prod.
        app (str): GitLab Project name.

    Returns:
        True when application.properties was found.
        False when application.properties needed to be created.
    """
    aws_env = boto3.session.Session(profile_name=env)
    s3client = aws_env.resource('s3')
    generated = get_details(app=app, env=env)

    archaius_bucket, app, project = generated.archaius()['s3'].split('/')[:-1]
    archaius_bucket = 'archaius-{env}'.format(env=env)
    archaius_file = ('{project}/{app}/application.properties').format(
        project=project,
        app=app)

    try:
        s3client.Object(archaius_bucket, archaius_file).get()
        LOG.info('Found: %(bucket)s/%(file)s', {'bucket': archaius_bucket,
                                                'file': archaius_file})
        return True
    except boto3.exceptions.botocore.client.ClientError:
        s3client.Object(archaius_bucket, archaius_file).put()
        LOG.info('Created: %(bucket)s/%(file)s', {'bucket': archaius_bucket,
                                                  'file': archaius_file})
        return False
