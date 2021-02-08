"""Create AWS Glue Jobs"""

import logging
import boto3
from tryagain import retries

from ..utils import get_details, get_properties, get_role_arn

LOG = logging.getLogger(__name__)


class AWSGlueJob:
    """Manipulate Glue Job."""

    def __init__(self, app, env, region, prop_path):
        """Glue Job object.

        Args:
            app (str): Application name
            env (str): Environment/Account
            region (str): AWS Region
            prop_path (str): Path of environment property file
        """
        self.app_name = app
        self.env = env
        self.region = region
        self.properties = get_properties(prop_path, env=self.env, region=self.region)
        generated = get_details(app=self.app_name)
        self.group = generated.data['project']
        app = self.settings['app']
        self.glue_timeout = app['glue_timeout']
        self.glue_retries = app['glue_retries']
        self.glue_command = app['glue_command']
        self.glue_connections = app['glue_connections']
        self.role = app.get('glue_role') or generated.iam()['glue_role']
        self.role_arn = get_role_arn(self.role, self.env, self.region)
        self.session = boto3.Session(profile_name=self.env, region_name=self.region)
        self.glue_client = self.session.client('glue')

    def _check_glue_job(self):
        """Check if glue job exists.

        Returns:
            True if function does exist
            False if function does not exist
        """
        exists = False
        try:
            self.glue_client.get_job(JobName=self.app_name)
            exists = True
        except boto3.exceptions.botocore.exceptions.ClientError:
            pass
        return exists

    @retries(max_attempts=3, wait=1, exceptions=(SystemExit))
    def update_glue_job(self):
        """Update existing Glue Job.
        """
        LOG.info('Updating Glue Job: %s', self.app_name)

        try:
            self.glue_client.update_job(
                JobName=self.app_name,
                JobUpdate={}
            )

            #     JobName=self.app_name,
            #     JobUpdate={
            #     Role=self.role_arn,
            #     Command=self.command,
            #     MaxRetries=int(self.timeout),
            #     Timeout=int(self.timeout),
            #     Tags={'app_group': self.group,
            #           'app_name': self.app_name}
            # )

        except boto3.exceptions.botocore.exceptions.ClientError:
            raise

        LOG.info("Successfully updated Glue configuration.")

    @retries(max_attempts=3, wait=1, exceptions=(SystemExit))
    def create_job(self):
        LOG.info('Creating glue job: %s', self.app_name)

        try:
            self.glue_client.create_job(
                Name=self.app_name,
                Role=self.role_arn,
                Command=self.command,
                MaxRetries=int(self.timeout),
                Timeout=int(self.timeout),
                Tags={'app_group': self.group,
                      'app_name': self.app_name})

        except boto3.exceptions.botocore.exceptions.ClientError:
            raise

        LOG.info("Successfully created Glue Job")

    def create_glue_job(self):
        """Create or update Glue function."""
        if self._check_glue_job():
            self.update_glue_job()
        else:
            self.create_job()
