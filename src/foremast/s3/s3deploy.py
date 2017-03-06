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

import json
import logging
import os

import boto3

from ..utils import get_properties, get_details

LOG = logging.getLogger(__name__)

class S3Deployment(object):
    """Handles uploading artifact to S3 and S3 deployment strategies"""

    def __init__(self, app, env, region, prop_path, artifact_path, artifact_version):
        """S3 deployment object.

        Args:
            app (str): Application name
            env (str): Environment/Account
            region (str): AWS Region
            prop_path (str): Path of environment property file
            artifact_path (str): Path to tar.gz artifact
        """
        self.app_name = app
        self.env = env
        self.region = region
        self.artifact_path = artifact_path
        self.version = artifact_version
        boto_sess = boto3.session.Session(profile_name=env)
        self.s3client = boto_sess.client('s3')
        generated = get_details(app=app, env=env)
        self.bucket = generated.s3_app_bucket()
        properties = get_properties(prop_path)
        self.s3props = properties[self.env]['s3']
        self.s3path = self.s3props['path']
        if self.s3path[0] == '/': #remove leading slash
            self.s3path[0] = ''

    def upload_artifacts(self):
        """Uploads the artifacts to S3 and copies to LATEST depending on strategy"""
        self._recursive_upload()
        self._copy_to_latest()

    def _recursive_upload(self):
        """Recursively uploads a directory and all files and subdirectories to S3"""
        for root, dirs, files in os.walk(self.artifact_path):
            trimmed_root = root.replace(self.artifact_path, "") #removes artifact path from root path
            for filename in files:
                abspath = os.path.join(root, filename)
                relpath = os.path.join(trimmed_root, filename)
                full_s3_path = "{}/{}/{}".format(self.s3path, self.version, relpath).replace('//', '/')
                with open(abspath) as f:
                    object_data = f.read()
                    LOG.debug("Uploading %s to %s", full_s3_path, self.bucket)
                    self.s3client.put_object(Body=object_data, Bucket=self.bucket, Key=full_s3_path)

    def _copy_to_latest(self):
        """Copies deployed version to LATEST directory"""

        copy_path = "{}/{}".format(self.s3path, self.version).replace('//', '/')
        prefix_path = "{}/".format(copy_path)
        version_string = "/{}/".format(self.version)

        resp = self.s3client.list_objects(Bucket=self.bucket, Prefix=prefix_path)
        allobjs = resp['Contents']

        for obj in allobjs:
            latest_path = obj['Key'].replace(version_string, '/LATEST/')
            print(latest_path)
            copy_source = {
                'Bucket': self.bucket,
                'Key': obj['Key']
            }
            self.s3client.copy(copy_source, self.bucket, latest_path)
            LOG.debug("Copied %s to %s", obj['Key'], latest_path)
        LOG.info("Copied Version %s to LATEST directory", self.version)
