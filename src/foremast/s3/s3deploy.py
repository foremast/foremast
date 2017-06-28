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
import os
import subprocess

from ..utils import get_properties, get_details
from ..exceptions import S3ArtifactNotFound

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
        self.properties = get_properties(prop_path)
        self.s3props = self.properties[self.env]['s3']
        generated = get_details(app=app, env=env)

        if self.s3props.get('shared_bucket_master'):
            self.bucket = generated.shared_s3_app_bucket()
            self.s3path = app
        elif self.s3props.get('shared_bucket_target'):
            shared_app = self.s3props['shared_bucket_target']
            newgenerated = get_details(app=shared_app, env=env)
            self.bucket = newgenerated.shared_s3_app_bucket()
            self.s3path = app
        else:
            self.bucket = generated.s3_app_bucket()
            self.s3path = self.s3props['path'].lstrip('/')

        self.s3_version_uri = ''
        self.s3_latest_uri = ''
        self.setup_pathing()

    def setup_pathing(self):
        """Formats pathing for S3 deployments"""
        self.s3_version_uri = self._path_formatter(self.version)
        self.s3_latest_uri = self._path_formatter("LATEST")
        self.s3_canary_uri = self._path_formatter("CANARY")

    def _path_formatter(self, suffix):
        """Formats the s3 path properly

        Args:
            suffix (str): suffix to add on to an s3 path
        
        Returns:
            str: formatted path
        """
        path_format = "{}/{}/{}"
        s3_format = "s3://{}"
        path = path_format.format(self.bucket, self.s3path, suffix)
        formatted_path = path.replace('//', '/') #removes configuration errors
        full_path = s3_format.format(formatted_path)
        return full_path

    def upload_artifacts(self):
        """Uploads the artifacts to S3 and copies to LATEST depending on strategy"""
        deploy_strategy = self.properties[self.env]["deploy_strategy"]
        if deploy_strategy == "highlander":
            self._upload_artifacts_to_version()
            self._sync_to_latest()
        elif deploy_strategy == "redblack":
            self._upload_artifacts_to_version()
        elif deploy_strategy == "canary":
            self._upload_artifacts_to_version()
            self._sync_to_canary()
        else:
            raise NotImplemented

    def promote_artifacts(self):
        """Promotes artifact version to LATEST"""
        self._sync_to_latest()

    def _upload_artifacts_to_version(self):
        """Recursively uploads a directory and all files and subdirectories to S3"""
        if not os.listdir(self.artifact_path) or not self.artifact_path:
            raise S3ArtifactNotFound
        cmd = 'aws s3 sync {} {} --delete --exact-timestamps --profile {}'.format(self.artifact_path,
                                                                                  self.s3_version_uri, self.env)
        p = subprocess.run(cmd, check=True, shell=True, stdout=subprocess.PIPE)
        LOG.debug("Upload Command Ouput: %s", p.stdout)
        LOG.info("Uploaded artifacts to %s bucket", self.bucket)

    def _sync_to_latest(self):
        """Uses AWS CLI to cp first then sync versioned directory to LATEST directory in S3"""
        cmd_cp = 'aws s3 cp {} {} --recursive --profile {}'.format(self.s3_version_uri, self.s3_latest_uri, self.env)
        # AWS CLI sync does not work as expected bucket to bucket with exact timestamp sync.
        cmd_sync = 'aws s3 sync {} {} --delete --exact-timestamps --profile {}'.format(
            self.s3_version_uri, self.s3_latest_uri, self.env)

        cp_result = subprocess.run(cmd_cp, check=True, shell=True, stdout=subprocess.PIPE)
        LOG.debug("Copy to latest before sync output: %s", cp_result.stdout)
        LOG.info("Copied version %s to %s", self.version, self.s3_latest_uri)

        sync_result = subprocess.run(cmd_sync, check=True, shell=True, stdout=subprocess.PIPE)
        LOG.debug("Sync to latest command output: %s", sync_result.stdout)
        LOG.info("Synced version %s to %s", self.version, self.s3_latest_uri)

    def _sync_to_canary(self):
        """Uses AWS CLI to cp first then sync versioned directory to CANARY directory in S3"""
        cmd_cp = 'aws s3 cp {} {} --recursive --profile {}'.format(self.s3_version_uri, self.s3_canary_uri, self.env)
        # AWS CLI sync does not work as expected bucket to bucket with exact timestamp sync.
        cmd_sync = 'aws s3 sync {} {} --delete --exact-timestamps --profile {}'.format(
            self.s3_version_uri, self.s3_canary_uri, self.env)

        cp_result = subprocess.run(cmd_cp, check=True, shell=True, stdout=subprocess.PIPE)
        LOG.debug("Copy to canary before sync output: %s", cp_result.stdout)
        LOG.info("Copied version %s to %s", self.version, self.s3_canary_uri)

        sync_result = subprocess.run(cmd_sync, check=True, shell=True, stdout=subprocess.PIPE)
        LOG.debug("Sync to canary command output: %s", sync_result.stdout)
        LOG.info("Synced version %s to %s", self.version, self.s3_canary_uri)
