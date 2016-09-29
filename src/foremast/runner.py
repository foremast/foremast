#!/usr/bin/env python
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
from foremast import (app, autoscaling_policy, awslambda, configs, consts, dns,
                      elb, iam, pipeline, s3, securitygroup, slacknotify,
                      utils)

from .args import add_debug

LOG = logging.getLogger(__name__)


class ForemastRunner(object):
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

        self.configs = configs.write_variables(app_configs=app_configs,
                                               out_file=self.raw_path,
                                               git_short=self.git_short)

    def create_app(self):
        """Create the spinnaker application."""
        utils.banner("Creating Spinnaker App")
        spinnakerapp = app.SpinnakerApp(app=self.app, email=self.email, project=self.group, repo=self.repo)
        spinnakerapp.create_app()

    def create_pipeline(self, onetime=None):
        """Create the spinnaker pipeline(s)."""
        utils.banner("Creating Pipeline")

        kwargs = {
            'app': self.app,
            'trigger_job': self.trigger_job,
            'prop_path': self.json_path,
            'base': None,
        }

        pipeline_type = self.configs['pipeline']['type']

        if pipeline_type not in consts.ALLOWED_TYPES:
            raise NotImplementedError('Pipeline type "{0}" not permitted.'.format(pipeline_type))

        if not onetime:
            if pipeline_type == 'ec2':
                spinnakerpipeline = pipeline.SpinnakerPipeline(**kwargs)
            elif pipeline_type == 'lambda':
                spinnakerpipeline = pipeline.SpinnakerPipelineLambda(**kwargs)
            else:
                raise NotImplementedError("Pipeline type is not implemented.")
        else:
            spinnakerpipeline = pipeline.SpinnakerPipelineOnetime(onetime=onetime, **kwargs)

        spinnakerpipeline.create_pipeline()

    def create_iam(self):
        """Create IAM resources."""
        utils.banner("Creating IAM")
        iam.create_iam_resources(env=self.env, app=self.app)

    def create_s3(self):
        """Create S3 bucket for Archaius."""
        utils.banner("Creating S3")
        s3.init_properties(env=self.env, app=self.app)

    def create_secgroups(self):
        """Create security groups as defined in the configs."""
        utils.banner("Creating Security Group")
        sgobj = securitygroup.SpinnakerSecurityGroup(app=self.app,
                                                     env=self.env,
                                                     region=self.region,
                                                     prop_path=self.json_path)
        sgobj.create_security_group()

    def create_awslambda(self):
        """Create security groups as defined in the configs."""
        utils.banner("Creating Lambda Function")
        awslambdaobj = awslambda.LambdaFunction(app=self.app,
                                                env=self.env,
                                                region=self.region,
                                                prop_path=self.json_path)
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
        dnsobj = dns.SpinnakerDns(app=self.app,
                                  env=self.env,
                                  region=self.region,
                                  prop_path=self.json_path,
                                  elb_subnet=elb_subnet)
        dnsobj.create_elb_dns()

    def create_autoscaling_policy(self):
        """Create Scaling Policy for app in environment"""
        utils.banner("Creating Scaling Policy")
        policyobj = autoscaling_policy.AutoScalingPolicy(app=self.app,
                                                         env=self.env,
                                                         region=self.region,
                                                         prop_path=self.json_path)
        policyobj.create_policy()

    def slack_notify(self):
        """Send out a slack notification."""
        utils.banner("Sending slack notification")

        if self.env.startswith("prod"):
            notify = slacknotify.SlackNotification(app=self.app, env=self.env, prop_path=self.json_path)
            notify.post_message()
        else:
            LOG.info("No slack message sent, not production environment")

    def cleanup(self):
        """Clean up generated files."""
        os.remove(self.raw_path)


def prepare_infrastructure():
    """Entry point for preparing the infrastructure in a specific env."""
    runner = ForemastRunner()

    runner.write_configs()
    runner.create_app()
    runner.create_iam()
    runner.create_s3()
    runner.create_secgroups()

    eureka = runner.configs[runner.env]['app']['eureka_enabled']
    deploy_type = runner.configs['pipeline']['type']

    if eureka:
        LOG.info("Eureka Enabled, skipping ELB and DNS setup")
    elif deploy_type == "lambda":
        LOG.info("Lambda Enabled, skipping ELB and DNS setup")
        runner.create_awslambda()
    else:
        LOG.info("No Eureka, running ELB and DNS setup")
        runner.create_elb()
        runner.create_dns()

    runner.slack_notify()
    runner.cleanup()


def prepare_app_pipeline():
    """Entry point for application setup and initial pipeline in Spinnaker."""
    runner = ForemastRunner()
    runner.create_app()
    runner.write_configs()
    runner.create_pipeline()
    runner.cleanup()


def prepare_onetime_pipeline():
    """Entry point for single use pipeline setup in the defined app."""
    runner = ForemastRunner()
    runner.write_configs()
    runner.create_pipeline(onetime=os.getenv('ENV'))
    runner.cleanup()


def create_scaling_policy():
    runner = ForemastRunner()
    runner.write_configs()
    runner.create_autoscaling_policy()
    runner.cleanup()


def rebuild_pipelines():
    """ Entry point for rebuilding pipelines. Can be used to rebuild all pipelines
        or a specific group """
    all_apps = utils.get_all_apps()
    rebuild_project = os.getenv("REBUILD_PROJECT")
    if rebuild_project is None:
        msg = 'No REBUILD_PROJECT variable found'
        LOG.fatal(msg)
        raise SystemExit('Error: {0}'.format(msg))

    for apps in all_apps:
        if 'repoProjectKey' not in apps:
            LOG.info("Skipping {}. No project key found".format(apps['name']))
            continue

        app_name = '{}/{}'.format(apps['repoProjectKey'], apps['repoSlug'])
        if (apps['repoProjectKey'].lower() == rebuild_project.lower() or rebuild_project == 'ALL'):
            os.environ["PROJECT"] = apps['repoProjectKey']
            os.environ["GIT_REPO"] = apps['repoSlug']
            LOG.info('Rebuilding pipelines for %s', app_name)
            runner = ForemastRunner()
            try:
                runner.write_configs()
                runner.create_pipeline()
                runner.cleanup()
            except Exception as error:
                LOG.warning('Error updating pipeline for %s', app_name)


def debug_flag():
    """Set logging level for entry points."""
    logging.basicConfig(format=consts.LOGGING_FORMAT)

    parser = argparse.ArgumentParser(description=debug_flag.__doc__)
    add_debug(parser)
    args = parser.parse_args()

    package, *_ = __package__.split('.')
    logging.getLogger(package).setLevel(args.debug)
