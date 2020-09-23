#!/usr/bin/env python
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
"""A runner for all of the spinnaker pipe modules.

Read environment variables from Jenkins:

    * EMAIL
    * ENV
    * GIT_REPO
    * PROJECT
    * REGION

Then run specific prepare jobs.
"""
import argparse
import logging
import os

import gogoutils

from . import (autoscaling_policy, awslambda, configs, consts, datapipeline, dns, elb, iam, pipeline, s3,
               scheduled_actions, securitygroup, slacknotify, utils)
from .gcp_iam import GcpIamResourceClient
from .app import SpinnakerApp
from .args import add_debug
from .cloudfunction.cloud_functions_client import CloudFunctionsClient
from .exceptions import ForemastError
from .utils.gcp_environment import GcpEnvironment
from tabulate import tabulate

LOG = logging.getLogger(__name__)


class ForemastRunner:
    """Wrap each pipes module in a way that is easy to invoke."""

    def __init__(self):
        """Setup the Runner for all Foremast modules."""
        debug_flag()

        self.email = os.getenv("EMAIL")
        self.env = os.getenv("ENV")
        self.group = os.getenv("PROJECT")
        self.region = os.getenv("REGION")
        self.repo = os.getenv("GIT_REPO")
        self.runway_dir = os.getenv("RUNWAY_DIR")
        self.artifact_path = os.getenv("ARTIFACT_PATH")
        self.artifact_version = os.getenv("ARTIFACT_VERSION")
        self.artifact_branch = os.getenv("ARTIFACT_BRANCH", "master")
        self.promote_stage = os.getenv("PROMOTE_STAGE", "latest")
        self.provider = os.getenv("PROVIDER", "aws")

        self.git_project = "{}/{}".format(self.group, self.repo)
        parsed = gogoutils.Parser(self.git_project)
        generated = gogoutils.Generator(*parsed.parse_url(), formats=consts.APP_FORMATS)

        self.app = generated.app_name()
        self.trigger_job = generated.jenkins()['name']
        self.git_short = generated.gitlab()['main']

        self.raw_path = "./raw.properties"
        self.json_path = self.raw_path + ".json"
        self.configs = None

    def write_configs(self):
        """Generate the configurations needed for pipes."""
        utils.banner("Generating Configs")
        if not self.runway_dir:
            app_configs = configs.process_git_configs(git_short=self.git_short)
        else:
            app_configs = configs.process_runway_configs(runway_dir=self.runway_dir)

        self.configs = configs.write_variables(
            app_configs=app_configs, out_file=self.raw_path, git_short=self.git_short)

    def create_app(self):
        """Create the spinnaker application."""
        utils.banner("Creating Spinnaker App")
        spinnakerapp = SpinnakerApp(
            provider=self.provider,
            app=self.app,
            email=self.email,
            project=self.group,
            repo=self.repo,
            pipeline_config=self.configs['pipeline'])
        spinnakerapp.create()

    def create_pipeline(self, onetime=None):
        """Create the spinnaker pipeline(s)."""
        utils.banner("Creating Pipeline")

        kwargs = {
            'app': self.app,
            'trigger_job': self.trigger_job,
            'prop_path': self.json_path,
            'base': None,
            'runway_dir': self.runway_dir,
        }

        pipeline_type = self.configs['pipeline']['type']

        if pipeline_type not in consts.ALLOWED_TYPES and pipeline_type not in consts.MANUAL_TYPES:
            raise NotImplementedError('Pipeline type "{0}" not permitted.'.format(pipeline_type))

        if not onetime:
            if pipeline_type == 'lambda':
                spinnakerpipeline = pipeline.SpinnakerPipelineLambda(**kwargs)
            elif pipeline_type == 's3':
                spinnakerpipeline = pipeline.SpinnakerPipelineS3(**kwargs)
            elif pipeline_type == 'datapipeline':
                spinnakerpipeline = pipeline.SpinnakerPipelineDataPipeline(**kwargs)
            elif pipeline_type in consts.MANUAL_TYPES:
                spinnakerpipeline = pipeline.SpinnakerPipelineManual(**kwargs)
            elif pipeline_type == 'cloudfunction':
                spinnakerpipeline = pipeline.SpinnakerPipelineCloudFunction(**kwargs)
            else:
                # Handles all other pipelines
                spinnakerpipeline = pipeline.SpinnakerPipeline(**kwargs)
        else:
            spinnakerpipeline = pipeline.SpinnakerPipelineOnetime(onetime=onetime, **kwargs)

        spinnakerpipeline.create_pipeline()

    def create_aws_iam(self):
        """Create AWS IAM resources."""
        utils.banner("Creating AWS IAM")
        iam.create_iam_resources(env=self.env, app=self.app)

    def create_gcp_iam(self):
        """Create GCP IAM resources."""
        utils.banner("Creating GCP IAM")
        env = self.get_current_gcp_env()
        gcp_iam_client = GcpIamResourceClient(env=env, app_name=self.app, group_name=self.group,
                                              repo_name=self.repo, configs=self.configs)
        gcp_iam_client.create_iam_resources()

    def create_archaius(self):
        """Create S3 bucket for Archaius."""
        utils.banner("Creating S3")
        s3.init_properties(env=self.env, app=self.app)

    def create_s3app(self):
        """Create S3 infra for s3 applications"""
        utils.banner("Creating S3 App Infrastructure")
        primary_region = self.configs['pipeline']['primary_region']
        s3obj = s3.S3Apps(app=self.app,
                          env=self.env,
                          region=self.region,
                          prop_path=self.json_path,
                          primary_region=primary_region)
        s3obj.create_bucket()

    def deploy_s3app(self):
        """Deploys artifacts contents to S3 bucket"""
        utils.banner("Deploying S3 App")
        primary_region = self.configs['pipeline']['primary_region']
        s3obj = s3.S3Deployment(
            app=self.app,
            env=self.env,
            region=self.region,
            prop_path=self.json_path,
            artifact_path=self.artifact_path,
            artifact_version=self.artifact_version,
            artifact_branch=self.artifact_branch,
            primary_region=primary_region)
        s3obj.upload_artifacts()

    def promote_s3app(self):
        """promotes S3 deployment to LATEST"""
        utils.banner("Promoting S3 App")
        primary_region = self.configs['pipeline']['primary_region']
        s3obj = s3.S3Deployment(
            app=self.app,
            env=self.env,
            region=self.region,
            prop_path=self.json_path,
            artifact_path=self.artifact_path,
            artifact_version=self.artifact_version,
            artifact_branch=self.artifact_branch,
            primary_region=primary_region)
        s3obj.promote_artifacts(promote_stage=self.promote_stage)

    def create_secgroups(self):
        """Create security groups as defined in the configs."""
        utils.banner("Creating Security Group")
        sgobj = securitygroup.SpinnakerSecurityGroup(
            app=self.app, env=self.env, region=self.region, prop_path=self.json_path)
        sgobj.create_security_group()

    def create_awslambda(self):
        """Create security groups as defined in the configs."""
        utils.banner("Creating Lambda Function")
        awslambdaobj = awslambda.LambdaFunction(
            app=self.app, env=self.env, region=self.region, prop_path=self.json_path)
        awslambdaobj.create_lambda_function()

        utils.banner("Creating Lambda Event")
        lambdaeventobj = awslambda.LambdaEvent(app=self.app, env=self.env, region=self.region, prop_path=self.json_path)
        lambdaeventobj.create_lambda_events()

    def create_elb(self):
        """Create the ELB for the defined environment."""
        utils.banner("Creating ELB")
        elbobj = elb.SpinnakerELB(app=self.app, env=self.env, region=self.region, prop_path=self.json_path)
        elbobj.create_elb()

    def create_dns(self):
        """Create DNS for the defined app and environment."""
        utils.banner("Creating DNS")
        elb_subnet = self.configs[self.env]['elb']['subnet_purpose']
        regions = self.configs[self.env]['regions']
        failover = self.configs[self.env]['dns']['failover_dns']
        primary_region = self.configs['pipeline']['primary_region']
        regionspecific_dns = self.configs[self.env]['dns']['region_specific']

        dnsobj = dns.SpinnakerDns(
            app=self.app, env=self.env, region=self.region, prop_path=self.json_path, elb_subnet=elb_subnet)

        if len(regions) > 1 and failover:
            dnsobj.create_elb_dns(regionspecific=True)
            dnsobj.create_failover_dns(primary_region=primary_region)
        else:
            if regionspecific_dns:
                dnsobj.create_elb_dns(regionspecific=True)

            if self.region == primary_region:
                dnsobj.create_elb_dns(regionspecific=False)

    def create_autoscaling_policy(self):
        """Create Scaling Policy for app in environment"""
        utils.banner("Creating Scaling Policy")
        policyobj = autoscaling_policy.AutoScalingPolicy(
            app=self.app, env=self.env, region=self.region, prop_path=self.json_path)
        policyobj.create_policy()

    def create_scheduled_actions(self):
        """Create Scheduled Actions for app in environment"""
        utils.banner("Creating Scheduled Actions")
        actionsobj = scheduled_actions.ScheduledActions(
            app=self.app, env=self.env, region=self.region, prop_path=self.json_path)
        actionsobj.create_scheduled_actions()

    def create_datapipeline(self):
        """Creates data pipeline and adds definition"""
        utils.banner("Creating Data Pipeline")
        dpobj = datapipeline.AWSDataPipeline(app=self.app, env=self.env, region=self.region, prop_path=self.json_path)
        dpobj.create_datapipeline()
        dpobj.set_pipeline_definition()
        if self.configs[self.env].get('datapipeline').get('activate_on_deploy'):
            dpobj.activate_pipeline()

    def deploy_cloudfunction(self):
        """Creates a Cloud Function"""
        utils.banner("Creating GCP Cloud Function")
        env = self.get_current_gcp_env()
        cloud_function_client = CloudFunctionsClient(self.app, env, self.configs)
        cloud_function_client.prepare_client()
        cloud_function_client.deploy_function(self.artifact_path, self.region)
        LOG.info("Finished deploying cloud function")

    def slack_notify(self):
        """Send out a slack notification."""
        utils.banner("Sending slack notification")

        if self.env.startswith("prod"):
            notify = slacknotify.SlackNotification(app=self.app, env=self.env, prop_path=self.json_path)
            notify.post_message()
        else:
            LOG.info("No slack message sent, not production environment")

    def get_current_gcp_env(self):
        """Gets the current GCP Environment
        Returns:
            GcpEnvironment, the current GCP environment
        Raises:
            ForemastError, when the current env name is not a known GCP Environment
        """
        all_gcp_envs = GcpEnvironment.get_environments_from_config()
        if self.env not in all_gcp_envs:
            raise ForemastError("GCP environment %s not found in configuration", self.env)
        return all_gcp_envs[self.env]

    def cleanup(self):
        """Clean up generated files."""
        os.remove(self.raw_path)


def prepare_infrastructure():
    """Entry point for preparing the infrastructure in a specific env."""

    runner = ForemastRunner()
    runner.write_configs()

    try:
        pipeline_type = runner.configs['pipeline']['type']
        if pipeline_type is None or pipeline_type.isspace():
            raise ForemastError("pipeline.type is required")
    except KeyError:
        raise ForemastError("pipeline.type is required")

    cloud_name = configs.get_cloud_for_pipeline_type(pipeline_type)

    if cloud_name == "gcp":
        LOG.info("Will create GCP Infrastructure for pipeline.type '%s'", pipeline_type)
        prepare_infrastructure_gcp(runner)
    elif cloud_name in "aws":
        LOG.info("Will create AWS Infrastructure for pipeline.type '%s'", pipeline_type)
        prepare_infrastructure_aws(runner, pipeline_type)
    else:
        error_message = ("pipeline.type of '{0}' is not supported. "
                         "If this is a manual pipeline it is required you specify the "
                         "pipeline type in AWS_MANUAL_TYPES or GCP_MANUAL_TYPES"
                         ).format(pipeline_type)
        raise ForemastError(error_message)


def prepare_infrastructure_gcp(runner: ForemastRunner):
    """Creates GCP infrastructure for a specific env."""
    # Always create IAM, this ensure svc account and permissions is done
    runner.create_gcp_iam()


def prepare_infrastructure_aws(runner, pipeline_type):
    """Creates AWS infrastructure for a specific env."""
    archaius = runner.configs[runner.env]['app']['archaius_enabled']
    eureka = runner.configs[runner.env]['app']['eureka_enabled']

    runner.create_app()

    if pipeline_type not in ['s3', 'datapipeline']:
        runner.create_aws_iam()
        # TODO: Refactor Archaius to be fully featured
        if archaius:
            runner.create_archaius()
        runner.create_secgroups()

    if eureka:
        LOG.info("Eureka Enabled, skipping ELB and DNS setup")
    elif pipeline_type == "lambda":
        LOG.info("Lambda Enabled, skipping ELB and DNS setup")
        runner.create_awslambda()
    elif pipeline_type == "s3":
        runner.create_s3app()
    elif pipeline_type == 'datapipeline':
        runner.create_datapipeline()
    else:
        LOG.info("No Eureka, running ELB and DNS setup")
        runner.create_elb()
        runner.create_dns()

    runner.slack_notify()
    runner.cleanup()


def describe_environments(args):
    """Prints a simple visual output of environments visible to Foremast"""
    if args.parsed.cloud_provider == "gcp":
        table = get_describe_gcp_environments()
    elif args.parsed.cloud_provider == "aws":
        table = get_describe_aws_environments()
    else:
        raise ForemastError("Cannot describe cloud '{}'".format(args.parsed.cloud_provider))

    output = tabulate(table[1], table[0], tablefmt=args.parsed.print_table_format)
    if args.parsed.print_to_file:
        file = open(args.parsed.print_to_file, "w")
        file.write(output)
        file.close()
        LOG.info("Saved printed table to %s", args.parsed.print_to_file)

    print(output)


def get_describe_gcp_environments():
    """Prints a simple visual output of GCP Environments visible to Foremast
    Returns:
        tuple: first the table headers, second the table values
    """
    table_header = ["Environment", "Project", "Permitted Groups"]
    env_table = list()
    all_envs = GcpEnvironment.get_environments_from_config()
    for env_name in all_envs:
        env = all_envs[env_name]
        env_table.append([env.name, env.service_account_project, "N/A"])
        all_projects = env.get_all_projects()
        for project in all_projects:
            if "foremast_groups" in project["labels"]:
                groups = project["labels"]["foremast_groups"]
            else:
                groups = "N/A"
            env_table.append([env.name, project["projectId"], groups])
    return table_header, env_table


def get_describe_aws_environments():
    """Prints a simple visual output of AWS environments configured in Foremast
    Returns:
        tuple: first the table headers, second the table values
    """
    table_header = ["Environment"]
    env_table = list()
    for env in configs.ENVS:
        env_table.append([env])

    return table_header, env_table


def prepare_app_pipeline():
    """Entry point for application setup and initial pipeline in Spinnaker."""
    runner = ForemastRunner()
    runner.write_configs()
    runner.create_app()
    runner.create_pipeline()
    runner.cleanup()


def prepare_onetime_pipeline():
    """Entry point for single use pipeline setup in the defined app."""
    runner = ForemastRunner()
    runner.write_configs()
    runner.create_pipeline(onetime=os.getenv('ENV'))
    runner.cleanup()


def create_scaling_policy():
    """Create Auto Scaling Policy for an Auto Scaling Group."""
    runner = ForemastRunner()
    runner.write_configs()
    runner.create_autoscaling_policy()
    runner.cleanup()


def create_scheduled_actions():
    """Create Scheduled Actions for an Auto Scaling Group."""
    runner = ForemastRunner()
    runner.write_configs()
    runner.create_scheduled_actions()
    runner.cleanup()


def rebuild_pipelines(*args):
    """Entry point for rebuilding pipelines.

    Use to rebuild all pipelines or a specific group.
    """
    rebuild_all = False
    rebuild_project = os.getenv("REBUILD_PROJECT")

    if args:
        LOG.debug('Incoming arguments: %s', args)
        command_args, *_ = args
        rebuild_all = command_args.parsed.all
        rebuild_project = command_args.parsed.project

    if rebuild_project == 'ALL':
        rebuild_all = True

    if rebuild_all:
        LOG.info('Rebuilding all projects.')
    elif rebuild_project is None:
        msg = 'No REBUILD_PROJECT variable found'
        LOG.fatal(msg)
        raise SystemExit('Error: {0}'.format(msg))
    else:
        LOG.info('Rebuilding project: %s', rebuild_project)

    all_apps = utils.get_all_apps()

    for apps in all_apps:
        if 'repoProjectKey' not in apps:
            LOG.info('Skipping %s. No project key found', apps['name'])
            continue

        app_name = '{}/{}'.format(apps['repoProjectKey'], apps['repoSlug'])
        if apps['repoProjectKey'].lower() == rebuild_project.lower() or rebuild_all:
            os.environ["PROJECT"] = apps['repoProjectKey']
            os.environ["GIT_REPO"] = apps['repoSlug']
            LOG.info('Rebuilding pipelines for %s', app_name)
            runner = ForemastRunner()
            try:
                runner.write_configs()
                runner.create_pipeline()
                runner.cleanup()
            except Exception:  # pylint: disable=broad-except
                LOG.warning('Error updating pipeline for %s', app_name)


def deploy_cloudfunction():
    """Deploys a GCP Cloud Function"""
    runner = ForemastRunner()
    runner.write_configs()
    runner.deploy_cloudfunction()


def deploy_s3app():
    """Entry point for application setup and s3 deployments"""
    runner = ForemastRunner()
    runner.write_configs()
    runner.deploy_s3app()


def promote_s3app():
    """Entry point for application setup and s3 promotions"""
    runner = ForemastRunner()
    runner.write_configs()
    runner.promote_s3app()


def debug_flag():
    """Set logging level for entry points."""
    logging.basicConfig(format=consts.LOGGING_FORMAT)

    parser = argparse.ArgumentParser(description=debug_flag.__doc__)
    add_debug(parser)
    args, _extra_args = parser.parse_known_args()

    package, *_ = __package__.split('.')
    logging.getLogger(package).setLevel(args.debug)
