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
"""Deploy artifacts to S3."""
import logging
import os
import subprocess

from ..exceptions import S3ArtifactNotFound
from ..utils import get_details, get_properties

LOG = logging.getLogger(__name__)


class S3Deployment(object):
    """Handle uploading artifacts to S3 and S3 deployment strategies."""

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
        self.properties = get_properties(prop_path, env=self.env, region=self.region)
        self.s3props = self.properties['s3']
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
        """Format pathing for S3 deployments."""
        self.s3_version_uri = self._path_formatter(self.version)
        self.s3_latest_uri = self._path_formatter("LATEST")
        self.s3_canary_uri = self._path_formatter("CANARY")
        self.s3_alpha_uri = self._path_formatter("ALPHA")
        self.s3_mirror_uri = self._path_formatter("MIRROR")

    def _path_formatter(self, suffix):
        """Format the s3 path properly.

        Args:
            suffix (str): suffix to add on to an s3 path

        Returns:
            str: formatted path

        """
        if suffix.lower() == "mirror":
            path_items = [self.bucket, self.s3path]
        else:
            path_items = [self.bucket, self.s3path, suffix]

        path = '/'.join(path_items)
        s3_format = "s3://{}"
        formatted_path = path.replace('//', '/')  # removes configuration errors
        full_path = s3_format.format(formatted_path)
        return full_path

    def upload_artifacts(self):
        """Upload artifacts to S3 and copy to correct path depending on strategy."""
        deploy_strategy = self.properties["deploy_strategy"]

        mirror = False
        if deploy_strategy == "mirror":
            mirror = True

        self._upload_artifacts_to_path(mirror=mirror)
        if deploy_strategy == "highlander":
            self._sync_to_uri(self.s3_latest_uri)
        elif deploy_strategy == "canary":
            self._sync_to_uri(self.s3_canary_uri)
        elif deploy_strategy == "alpha":
            self._sync_to_uri(self.s3_alpha_uri)
        elif deploy_strategy == "mirror":
            pass  # Nothing extra needed for mirror deployments
        else:
            raise NotImplementedError

    def promote_artifacts(self, promote_stage='latest'):
        """Promote artifact version to dest.

        Args:
            promote_stage (string): Stage that is being promoted
        """
        if promote_stage.lower() == 'alpha':
            self._sync_to_uri(self.s3_canary_uri)
        elif promote_stage.lower() == 'canary':
            self._sync_to_uri(self.s3_latest_uri)
        else:
            self._sync_to_uri(self.s3_latest_uri)

    def _get_upload_cmd(self, mirror=False):
        """Generate the S3 CLI upload command

        Args:
            mirror (bool): If true, uses a flat directory structure instead of nesting under a version.

        Returns:
            str: The full CLI command to run.
        """
        if mirror:
            dest_uri = self.s3_mirror_uri
        else:
            dest_uri = self.s3_version_uri

        cmd = 'aws s3 sync {} {} --delete --exact-timestamps --profile {}'.format(self.artifact_path,
                                                                                  dest_uri, self.env)
        return cmd

    def _upload_artifacts_to_path(self, mirror=False):
        """Recursively upload directory contents to S3.

        Args:
            mirror (bool): If true, uses a flat directory structure instead of nesting under a version.
        """
        if not os.listdir(self.artifact_path) or not self.artifact_path:
            raise S3ArtifactNotFound

        uploaded = False
        if self.s3props.get("content_metadata"):
            LOG.info("Uploading in multiple parts to set metadata")
            uploaded = self.content_metadata_uploads(mirror=mirror)

        if not uploaded:
            cmd = self._get_upload_cmd(mirror=mirror)
            result = subprocess.run(cmd, check=True, shell=True, stdout=subprocess.PIPE)
            LOG.debug("Upload Command Ouput: %s", result.stdout)

        LOG.info("Uploaded artifacts to %s bucket", self.bucket)

    def content_metadata_uploads(self, mirror=False):
        """Finds all specified encoded directories and uploads in multiple parts,
        setting metadata for objects.

        Args:
            mirror (bool): If true, uses a flat directory structure instead of nesting under a version.

        Returns:
            bool: True if uploaded
        """
        excludes_str = ''
        includes_cmds = []
        cmd_base = self._get_upload_cmd(mirror=mirror)

        for content in self.s3props.get('content_metadata'):
            full_path = os.path.join(self.artifact_path, content['path'])
            if not os.listdir(full_path):
                raise S3ArtifactNotFound

            excludes_str += '--exclude "{}/*" '.format(content['path'])
            include_cmd = '{} --exclude "*", --include "{}/*"'.format(cmd_base, content['path'])
            include_cmd += ' --content-encoding {} --metadata-directive REPLACE'.format(content['content-encoding'])
            includes_cmds.append(include_cmd)

        exclude_cmd = '{} {}'.format(cmd_base, excludes_str)
        result = subprocess.run(exclude_cmd, check=True, shell=True, stdout=subprocess.PIPE)
        LOG.info("Uploaded files without metadata with command: %s", exclude_cmd)
        LOG.debug("Upload Command Output: %s", result.stdout)

        for include_cmd in includes_cmds:
            result = subprocess.run(include_cmd, check=True, shell=True, stdout=subprocess.PIPE)
            LOG.info("Uploaded files with metadata with command: %s", include_cmd)
            LOG.debug("Upload Command Output: %s", result.stdout)

        return True

    def _sync_to_uri(self, uri):
        """Copy and sync versioned directory to uri in S3.

        Args:
            uri (str): S3 URI to sync version to.
        """
        cmd_cp = 'aws s3 cp {} {} --recursive --profile {}'.format(self.s3_version_uri, uri, self.env)
        # AWS CLI sync does not work as expected bucket to bucket with exact timestamp sync.
        cmd_sync = 'aws s3 sync {} {} --delete --exact-timestamps --profile {}'.format(
            self.s3_version_uri, uri, self.env)

        cp_result = subprocess.run(cmd_cp, check=True, shell=True, stdout=subprocess.PIPE)
        LOG.debug("Copy to %s before sync output: %s", uri, cp_result.stdout)
        LOG.info("Copied version %s to %s", self.version, uri)

        sync_result = subprocess.run(cmd_sync, check=True, shell=True, stdout=subprocess.PIPE)
        LOG.debug("Sync to %s command output: %s", uri, sync_result.stdout)
        LOG.info("Synced version %s to %s", self.version, uri)
