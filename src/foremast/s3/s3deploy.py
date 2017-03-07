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

import logging
import subprocess

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
        generated = get_details(app=app, env=env)
        self.bucket = generated.s3_app_bucket()
        self.properties = get_properties(prop_path)
        self.s3props = self.properties[self.env]['s3']
        self.s3path = self.s3props['path'].lstrip('/')
        self.s3_version_uri = ''
        self.s3_latest_uri = ''
        self.setup_pathing()

    def setup_pathing(self):
        """Formats pathing for S3 deployments"""
        path_format = "{}/{}/{}"
        s3_format = "s3://{}"
        version_path = path_format.format(self.bucket, self.s3path, self.version).replace('//', '/')
        latest_path = path_format.format(self.bucket, self.s3path, "LATEST").replace('//', '/')
        self.s3_version_uri = s3_format.format(version_path)
        self.s3_latest_uri = s3_format.format(latest_path)

    def upload_artifacts(self):
        """Uploads the artifacts to S3 and copies to LATEST depending on strategy"""
        deploy_strategy = self.properties[self.env]["deploy_strategy"]
        if deploy_strategy == "highlander":
            self._upload_artifacts_to_version()
            self._sync_to_latest()
        elif deploy_strategy == "redblack":
            self._upload_artifacts_to_version()
        else:
            raise NotImplemented

    def promote_artifacts(self):
        """Promotes artifact version to LATEST"""
        self._sync_to_latest()

    def _upload_artifacts_to_version(self):
        """Recursively uploads a directory and all files and subdirectories to S3"""
        cmd = 'aws s3 sync {} {} --delete --profile {}'.format(self.artifact_path, self.s3_version_uri, self.env)
        p = subprocess.run(cmd, check=True, shell=True, stdout=subprocess.PIPE)
        LOG.debug("Upload Command Ouput: %s", p.stdout)
        LOG.info("Uploaded artifacts to %s bucket", self.bucket)

    def _sync_to_latest(self):
        """Uses AWS CLI to sync versioned directory to LATEST directory in S3"""
        cmd = 'aws s3 sync {} {} --delete --profile {}'.format(self.s3_version_uri, self.s3_latest_uri, self.env)
        p = subprocess.run(cmd, check=True, shell=True, stdout=subprocess.PIPE)
        LOG.debug("Sync to latest command output: %s", p.stdout)
        LOG.info("Copied version %s to LATEST", self.version)
