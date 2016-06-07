#!/usr/bin/env python
"""A runner for all of the spinnaker pipe modules.

Read environment variables from Jenkins:

    * EMAIL
    * ENV
    * GIT_REPO
    * PROJECT
    * REGION

Then run specific prepare jobs.
"""
import logging
import os

import gogoutils

from foremast import (app, configs, consts, dns, elb, iam, pipeline, s3,
                      securitygroup, slacknotify, utils)

LOG = logging.getLogger(__name__)
logging.basicConfig(format=consts.LOGGING_FORMAT)
logging.getLogger("foremast").setLevel(logging.INFO)


class ForemastRunner(object):
    """Wrap each pipes module in a way that is easy to invoke."""

    def __init__(self):
        """Setup the Runner for all Foremast modules."""
        self.email = os.getenv("EMAIL")
        self.env = os.getenv("ENV")
        self.group = os.getenv("PROJECT")
        self.region = os.getenv("REGION")
        self.repo = os.getenv("GIT_REPO")

        self.git_project = "{}/{}".format(self.group, self.repo)
        parsed = gogoutils.Parser(self.git_project)
        generated = gogoutils.Generator(*parsed.parse_url())

        self.app = generated.app
        self.trigger_job = generated.jenkins()['name']
        self.git_short = generated.gitlab()['main']

        self.gitlab_token_path = os.path.expanduser('~/.aws/git.token')
        self.raw_path = "./raw.properties"
        self.json_path = self.raw_path + ".json"
        self.configs = None

    def write_configs(self):
        """Generate the configurations needed for pipes."""
        utils.banner("Generating Configs")
        self.configs = configs.process_git_configs(
            git_short=self.git_short,
            token_file=self.gitlab_token_path)
        configs.write_variables(app_configs=self.configs,
                                out_file=self.raw_path,
                                git_short=self.git_short)

    def create_app(self):
        """Create the spinnaker application."""
        utils.banner("Creating Spinnaker App")
        spinnakerapp = app.SpinnakerApp(app=self.app,
                                        email=self.email,
                                        project=self.group,
                                        repo=self.repo)
        spinnakerapp.create_app()

    def create_pipeline(self, onetime=None):
        """Create the spinnaker pipeline(s)."""
        utils.banner("Creating Pipeline")

        if not onetime:
            spinnakerpipeline = pipeline.SpinnakerPipeline(
                app=self.app,
                trigger_job=self.trigger_job,
                prop_path=self.json_path,
                base=None,
                token_file=self.gitlab_token_path)
        else:
            spinnakerpipeline = pipeline.SpinnakerPipelineOnetime(
                app=self.app,
                trigger_job=self.trigger_job,
                prop_path=self.json_path,
                base=None,
                token_file=self.gitlab_token_path,
                onetime=onetime)

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

    def create_elb(self):
        """Create the ELB for the defined environment."""
        utils.banner("Creating ELB")
        elbobj = elb.SpinnakerELB(app=self.app,
                                  env=self.env,
                                  region=self.region,
                                  prop_path=self.json_path)
        elbobj.create_elb()

    def create_dns(self):
        """Create DNS for the defined app and environment."""
        utils.banner("Creating DNS")
        elb_subnet = self.configs[self.env]['elb']['subnet_purpose']
        dnsobj = dns.SpinnakerDns(app=self.app,
                                  env=self.env,
                                  region=self.region,
                                  elb_subnet=elb_subnet)
        dnsobj.create_elb_dns()

    def slack_notify(self):
        """Send out a slack notification."""
        utils.banner("Sending slack notification")

        if self.env.startswith("prod"):
            notify = slacknotify.SlackNotification(app=self.app,
                                                   env=self.env,
                                                   prop_path=self.json_path)
            notify.post_message()
        else:
            LOG.info("No slack message sent, not production environment")

    def cleanup(self):
        """Clean up generated files."""
        os.remove(self.raw_path)

    def prepare_infrastructure(self):
        """Prepare the infrastructure in a specific env."""
        self.write_configs()
        self.create_iam()
        self.create_s3()
        self.create_secgroups()

        try:
            eureka = self.configs[self.env]['app']['eureka_enabled']
        except KeyError:
            eureka = False

        if eureka:
            LOG.info("Eureka Enabled, skipping ELB and DNS setup")
        else:
            LOG.info("No Eureka, running ELB and DNS setup")
            self.create_elb()
            self.create_dns()
            LOG.info("Eureka Enabled, skipping ELB and DNS setup")

        self.slack_notify()
        self.cleanup()

    def prepare_app_pipeline(self):
        """Setup the application and initial pipeline in Spinnaker."""
        self.create_app()
        self.write_configs()
        self.create_pipeline()
        self.cleanup()

    def prepare_onetime_pipeline(self, onetime=None):
        """Setup a single use pipeline in the defined app."""
        self.write_configs()
        self.create_pipeline(onetime=onetime)
        self.cleanup()


def prepare_infrastructure():
    """Entry point for preparing the infrastructure in a specific env."""
    runner = ForemastRunner()
    runner.prepare_infrastructure()


def prepare_app_pipeline():
    """Entry point for application setup and initial pipeline in Spinnaker."""
    runner = ForemastRunner()
    runner.prepare_app_pipeline()


def prepare_onetime_pipeline():
    """Entry point for single use pipeline setup in the defined app."""
    runner = ForemastRunner()
    runner.prepare_onetime_pipeline(onetime=os.getenv('ENV'))
