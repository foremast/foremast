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

"""Destroy any S3 Resources."""
import logging

import boto3

from ...utils import get_details

LOG = logging.getLogger(__name__)


def destroy_s3(app='', env='dev', **_):
    """Destroy S3 Resources for _app_ in _env_.

    Args:
        app (str): Application name
        env (str): Deployment environment/account name

    Returns:
        boolean: True if destroyed sucessfully
    """
    session = boto3.Session(profile_name=env)
    client = session.resource('s3')

    generated = get_details(app=app, env=env)
    archaius = generated.archaius()

    bucket = client.Bucket(archaius['bucket'])

    for item in bucket.objects.filter(Prefix=archaius['path']):
        item.Object().delete()
        LOG.info('Deleted: %s/%s', item.bucket_name, item.key)

    return True
