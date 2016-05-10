"""Destroy any S3 Resources."""
import logging

import boto3

from ...utils import get_app_details

LOG = logging.getLogger(__name__)


def destroy_s3(app='', env='dev', **_):
    """Destroy S3 Resources for _app_ in _env_."""
    session = boto3.Session(profile_name=env)
    client = session.resource('s3')

    generated = get_app_details.get_details(app=app, env=env)
    archaius = generated.archaius()

    bucket = client.Bucket(archaius['bucket'])

    for item in bucket.objects.filter(Prefix=archaius['path']):
        item.Object().delete()
        LOG.info('Deleted: %s/%s', item.bucket_name, item.key)

    return True
