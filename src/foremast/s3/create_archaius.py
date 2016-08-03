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

"""Archaius functions for deployment."""
import logging

import boto3

from ..utils import get_details

LOG = logging.getLogger(__name__)


def init_properties(env='dev', app='unnecessary', **_):
    """Make sure _application.properties_ file exists in S3.

    For Applications with Archaius support, there needs to be a file where the
    cloud environment variable points to.

    Args:
        env (str): Deployment environment/account, i.e. dev, stage, prod.
        app (str): GitLab Project name.

    Returns:
        True when application.properties was found.
        False when application.properties needed to be created.
    """
    aws_env = boto3.session.Session(profile_name=env)
    s3client = aws_env.resource('s3')

    generated = get_details(app=app, env=env)
    archaius = generated.archaius()

    archaius_file = ('{path}/application.properties').format(
        path=archaius['path'])

    try:
        s3client.Object(archaius['bucket'], archaius_file).get()
        LOG.info('Found: %(bucket)s/%(file)s', {'bucket': archaius['bucket'],
                                                'file': archaius_file})
        return True
    except boto3.exceptions.botocore.client.ClientError:
        s3client.Object(archaius['bucket'], archaius_file).put()
        LOG.info('Created: %(bucket)s/%(file)s', {'bucket': archaius['bucket'],
                                                  'file': archaius_file})
        return False
