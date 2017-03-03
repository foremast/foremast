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

import boto3

from ..utils import get_properties, get_details

LOG = logging.getLogger(__name__)

class S3Apps(object):
    """Handles infrastructure around depolying static content to S3. Setups Bucket and Policy"""

    def __init__(self, app, env, region, prop_path):
        """S3 application object. Setups Bucket and policies for S3 applications.

        Args:
            app (str): Application name
            env (str): Environment/Account
            region (str): AWS Region
            prop_path (str): Path of environment property file
        """
        self.app_name = app
        self.env = env
        self.region = region
        boto_sess = boto3.session.Session(profile_name=env)
        self.s3client = boto_sess.client('s3')
        generated = get_details(app=app, env=env)
        self.bucket = generated.s3_app_bucket()
        properties = get_properties(prop_path)
        self.s3props = properties[self.env]['s3']

    def create_bucket(self):
        """Creates or updates bucket based on app name"""
        resp = self.s3client.create_bucket(
            ACL=self.s3props['bucket_acl'],
            Bucket=self.bucket
        )
        LOG.info('%s - S3 Bucket Upserted', self.bucket)
        if self.s3props['bucket_policy']:
            self._attach_bucket_policy()

    def _attach_bucket_policy(self):
        """attaches a bucket policy to app bucket"""
        policy_str = json.dumps(self.s3props['bucket_policy'])
        resp = self.s3client.put_bucket_policy(Bucket=self.bucket,
                                               Policy=policy_str)
        LOG.info('S3 Bucket Policy Attached')
