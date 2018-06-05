#   Foremast - Pipeline Tooling
#
#   Copyright 2018 Gogo, LLC
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
"""S3 web application infrastructure."""
import json
import logging

import boto3
from botocore.client import ClientError

from ..exceptions import S3SharedBucketNotFound
from ..utils import generate_s3_tags, get_details, get_dns_zone_ids, get_properties, update_dns_zone_record

LOG = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class S3Apps(object):
    """Configure infrastructure and policies for S3 web applications."""

    def __init__(self, app, env, region, prop_path, primary_region='us-east-1'):
        """S3 application object. Setups Bucket and policies for S3 applications.

        Args:
            app (str): Application name
            env (str): Environment/Account
            region (str): AWS Region
            prop_path (str): Path of environment property file
            primary_region (str): The primary region for the application.
        """
        self.app_name = app
        self.env = env
        self.region = region
        boto_sess = boto3.session.Session(profile_name=env)
        self.s3client = boto_sess.client('s3')
        self.generated = get_details(app=app, env=env, region=self.region)
        self.properties = get_properties(prop_path, env=self.env, region=self.region)
        self.s3props = self.properties['s3']
        self.group = self.generated.project

        include_region = True
        if self.region == primary_region:
            include_region = False
        if self.s3props.get('shared_bucket_master'):
            self.bucket = self.generated.shared_s3_app_bucket(include_region=include_region)
        elif self.s3props.get('shared_bucket_target'):
            shared_app = self.s3props['shared_bucket_target']
            newgenerated = get_details(app=shared_app, env=env, region=self.region)
            self.bucket = newgenerated.shared_s3_app_bucket(include_region=include_region)
        else:
            self.bucket = self.generated.s3_app_bucket(include_region=include_region)

    def create_bucket(self):
        """Create or update bucket based on app name."""
        bucket_exists = self._bucket_exists()
        if self.s3props.get('shared_bucket_target'):
            if bucket_exists:
                LOG.info('App uses shared bucket - %s ', self.bucket)
            else:
                LOG.error("Shared bucket %s does not exist", self.bucket)
                raise S3SharedBucketNotFound
        else:
            if self.region == 'us-east-1':
                _response = self.s3client.create_bucket(ACL=self.s3props['bucket_acl'], Bucket=self.bucket)
            else:
                if not bucket_exists:
                    _response = self.s3client.create_bucket(ACL=self.s3props['bucket_acl'], Bucket=self.bucket,
                                                            CreateBucketConfiguration={
                                                                'LocationConstraint': self.region})
                else:
                    _response = "bucket already exists, skipping create for non-standard region buckets."
            LOG.debug('Response creating bucket: %s', _response)
            LOG.info('%s - S3 Bucket Upserted', self.bucket)
            self._put_bucket_policy()
            self._put_bucket_website()
            self._put_bucket_logging()
            self._put_bucket_lifecycle()
            self._put_bucket_versioning()
            self._put_bucket_encryption()
            self._put_bucket_tagging()

    def _bucket_exists(self):
        """Check if the bucket exists."""
        try:
            self.s3client.get_bucket_location(Bucket=self.bucket)
            return True
        except ClientError as error:
            LOG.error(error)
            return False

    def _put_bucket_policy(self):
        """Attach a bucket policy to app bucket."""
        if self.s3props['bucket_policy']:
            policy_str = json.dumps(self.s3props['bucket_policy'])
            _response = self.s3client.put_bucket_policy(Bucket=self.bucket, Policy=policy_str)
        else:
            _response = self.s3client.delete_bucket_policy(Bucket=self.bucket)
        LOG.debug('Response adding bucket policy: %s', _response)
        LOG.info('S3 Bucket Policy Attached')

    def _put_bucket_website(self):
        """Configure static website on S3 bucket."""
        if self.s3props['website']['enabled']:
            website_config = {
                'ErrorDocument': {
                    'Key': self.s3props['website']['error_document']
                },
                'IndexDocument': {
                    'Suffix': self.s3props['website']['index_suffix']
                }
            }
            _response = self.s3client.put_bucket_website(Bucket=self.bucket, WebsiteConfiguration=website_config)
            self._put_bucket_cors()
            self._set_bucket_dns()
        else:
            _response = self.s3client.delete_bucket_website(Bucket=self.bucket)
            self._put_bucket_cors()
        LOG.debug('Response setting up S3 website: %s', _response)
        LOG.info('S3 website settings updated')

    def _set_bucket_dns(self):
        """Create CNAME for S3 endpoint."""
        # Different regions have different s3 endpoint formats
        dotformat_regions = ["eu-west-2", "eu-central-1", "ap-northeast-2", "ap-south-1", "ca-central-1", "us-east-2"]
        if self.region in dotformat_regions:
            s3_endpoint = "{0}.s3-website.{1}.amazonaws.com".format(self.bucket, self.region)
        else:
            s3_endpoint = "{0}.s3-website-{1}.amazonaws.com".format(self.bucket, self.region)

        zone_ids = get_dns_zone_ids(env=self.env, facing="public")
        dns_kwargs = {
            'dns_name': self.bucket,
            'dns_name_aws': s3_endpoint,
            'dns_ttl': self.properties['dns']['ttl']
        }

        for zone_id in zone_ids:
            LOG.debug('zone_id: %s', zone_id)
            update_dns_zone_record(self.env, zone_id, **dns_kwargs)
        LOG.info("Created DNS %s for Bucket", self.bucket)

    def _put_bucket_cors(self):
        """Adds bucket cors configuration."""
        if self.s3props['cors']['enabled'] and self.s3props['website']['enabled']:
            cors_config = {}
            cors_rules = []
            for each_rule in self.s3props['cors']['cors_rules']:
                cors_rules.append({
                    'AllowedHeaders': each_rule['cors_headers'],
                    'AllowedMethods': each_rule['cors_methods'],
                    'AllowedOrigins': each_rule['cors_origins'],
                    'ExposeHeaders': each_rule['cors_expose_headers'],
                    'MaxAgeSeconds': each_rule['cors_max_age']
                })
            cors_config = {
                'CORSRules': cors_rules
            }
            LOG.debug(cors_config)
            _response = self.s3client.put_bucket_cors(Bucket=self.bucket, CORSConfiguration=cors_config)
        else:
            _response = self.s3client.delete_bucket_cors(Bucket=self.bucket)
        LOG.debug('Response setting up S3 CORS: %s', _response)
        LOG.info('S3 CORS configuration updated')

    def _put_bucket_encryption(self):
        """Adds bucket encryption configuration."""
        if self.s3props['encryption']['enabled']:
            encryption_config = {'Rules': [{}]}
            encryption_config = {
                'Rules': self.s3props['encryption']['encryption_rules']
            }
            LOG.debug(encryption_config)
            _response = self.s3client.put_bucket_encryption(Bucket=self.bucket,
                                                            ServerSideEncryptionConfiguration=encryption_config)
        else:
            _response = self.s3client.delete_bucket_encryption(Bucket=self.bucket)
        LOG.debug('Response setting up S3 encryption: %s', _response)
        LOG.info('S3 encryption configuration updated')

    def _put_bucket_lifecycle(self):
        """Adds bucket lifecycle configuration."""
        status = 'deleted'
        if self.s3props['lifecycle']['enabled']:
            lifecycle_config = {
                'Rules': self.s3props['lifecycle']['lifecycle_rules']
            }
            LOG.debug('Lifecycle Config: %s', lifecycle_config)
            _response = self.s3client.put_bucket_lifecycle_configuration(Bucket=self.bucket,
                                                                         LifecycleConfiguration=lifecycle_config)
            status = 'applied'
        else:
            _response = self.s3client.delete_bucket_lifecycle(Bucket=self.bucket)
        LOG.debug('Response setting up S3 lifecycle: %s', _response)
        LOG.info('S3 lifecycle configuration %s', status)

    def _put_bucket_logging(self):
        """Adds bucket logging policy to bucket for s3 access requests"""
        logging_config = {}
        if self.s3props['logging']['enabled']:
            logging_config = {
                'LoggingEnabled': {
                    'TargetBucket': self.s3props['logging']['logging_bucket'],
                    'TargetGrants': self.s3props['logging']['logging_grants'],
                    'TargetPrefix': self.s3props['logging']['logging_bucket_prefix']
                }
            }
        _response = self.s3client.put_bucket_logging(Bucket=self.bucket, BucketLoggingStatus=logging_config)
        LOG.debug('Response setting up S3 logging: %s', _response)
        LOG.info('S3 logging configuration updated')

    def _put_bucket_tagging(self):
        """Add bucket tags to bucket."""
        all_tags = self.s3props['tagging']['tags']
        all_tags.update({'app_group': self.group, 'app_name': self.app_name})
        tag_set = generate_s3_tags.generated_tag_data(all_tags)

        tagging_config = {'TagSet': tag_set}

        self.s3client.put_bucket_tagging(Bucket=self.bucket, Tagging=tagging_config)
        LOG.info("Adding tagging %s for Bucket", tag_set)

    def _put_bucket_versioning(self):
        """Adds bucket versioning policy to bucket"""
        status = 'Suspended'
        if self.s3props['versioning']['enabled']:
            status = 'Enabled'

        versioning_config = {
            'MFADelete': self.s3props['versioning']['mfa_delete'],
            'Status': status
        }

        _response = self.s3client.put_bucket_versioning(Bucket=self.bucket, VersioningConfiguration=versioning_config)
        LOG.debug('Response setting up S3 versioning: %s', _response)
        LOG.info('S3 versioning configuration updated')
