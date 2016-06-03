#!/usr/bin/env python 
import argparse
import logging
import os

from foremast import (configs, consts, iam, s3, 
securitygroup, elb, dns, slacknotify, app, pipeline)
import gogoutils

LOG = logging.getLogger(__name__)
logging.basicConfig(format=consts.LOGGING_FORMAT)
logging.getLogger("foremast").setLevel(logging.INFO)

class ForemastRunner:
    def __init__(self, group=None, repo=None, env=None,
                region=None, email=None):
        """ Setups the Runner for all Foremast modules

        Args:
            group (str): Gitlab group of the application
            repo (str): The application repository name
            env (str): Deployment environment, dev/stage/prod etc
            region (str): AWS region (us-east-1)
        """
        self.group = group
        self.repo = repo
        self.git_project = "{}/{}".format(group, repo)
        parsed = gogoutils.Parser(self.git_project)
        generated = gogoutils.Generator(*parsed.parse_url())
        self.app = generated.app
        self.trigger_job = generated.jenkins()['name']
        self.git_short = generated.gitlab()['main']
        self.gitlab_token_path = os.environ["HOME"]+ "/.aws/git.token"
        self.raw_path = "./raw.properties"
        self.json_path = self.raw_path + ".json"
        self.env = env
        self.region = region
        self.email= email
        self.configs = None


    def write_configs(self):
        self.banner("Generating Configs")
        if not self.gitlab_token_path:
            raise SystemExit('Must provide private token file as well.')
        self.configs = configs.process_git_configs(git_short=self.git_short,
                                      token_file=self.gitlab_token_path)

        configs.write_variables(app_configs=self.configs,
                        out_file=self.raw_path,
                        git_short=self.git_short)


    def create_app(self):
        self.banner("Creating Spinnaker App")
        spinnakerapp = app.SpinnakerApp(app=self.app,
                                        email=self.email,
                                        project=self.group,
                                        repo=self.repo)
        spinnakerapp.create_app()


    def create_pipeline(self, onetime=None):
        self.banner("Creating Pipeline")
        if not onetime:
            spinnakerpipeline = pipeline.SpinnakerPipeline(app=self.app,
                                                       trigger_job=self.trigger_job,
                                                       prop_path=self.json_path,
                                                       base=None,
                                                       token_file=self.gitlab_token_path)
        else:
             spinnakerpipeline = pipeline.SpinnakerPipelineOnetime(app=self.app,
                                                       trigger_job=self.trigger_job,
                                                       prop_path=self.json_path,
                                                       base=None,
                                                       token_file=self.gitlab_token_path,
                                                       onetime=onetime)

        spinnakerpipeline.create_pipeline()

    def create_iam(self):
        self.banner("Creating IAM")
        iam.create_iam_resources(env=self.env, app=self.app)

    
    def create_s3(self):
        self.banner("Creating S3")
        s3.init_properties(env=self.env, app=self.app)

    
    def create_secgroups(self):
        self.banner("Creating Security Group")
        sgobj = securitygroup.SpinnakerSecurityGroup(app=self.app,
                                                    env=self.env,
                                                    region=self.region,
                                                    prop_path=self.json_path)
        sgobj.create_security_group()

   
    def create_elb(self):
        self.banner("Creating ELB")
        elbobj = elb.SpinnakerELB(app=self.app,
                                env=self.env,
                                region=self.region,
                                prop_path=self.json_path)
        elbobj.create_elb()


    def create_dns(self):
        self.banner("Creating DNS")
        elb_type = self.configs[self.env]['elb']['subnet_purpose']
        dnsobj = dns.SpinnakerDns(app=self.app,
                                     env=self.env,
                                     region=self.region,
                                     elb_subnet=elb_subnet)
        dnsobj.create_elb_dns()

    def slack_notify(self):
        self.banner("Sending slack notification")
        if self.env.startswith("prod"):
            notify = slacknotify.SlackNotification(app=self.app,
                                                  env=self.env,
                                                  prop_path=self.json_path)
            notify.post_message()
        else:
            LOG.info("No slack message sent, not production environment")

    def banner(self, notice):
        """ Prints a banner for seperating tasks """
        print("\n===============================")
        print(notice)
        print("===============================\n")


    def cleanup(self):
        os.remove(self.raw_path)
   

    def prepare_infrastructure(self):
        """ This runs everything necessary to prepare the infrastructure in a specific env """
        self.write_configs()
        self.create_iam()
        self.create_s3()
        self.create_secgroups()
        if not self.configs[self.env]['app']['eureka_enabled']:
            LOG.info("No Eureka, running ELB and DNS setup")
            self.create_elb()
            self.create_dns()
        else:
            LOG.info("Eureka Enabled, skipping ELB and DNS setup")
        self.slack_notify()
        self.cleanup()

    def prepare_app_pipeline(self):
        self.create_app()
        self.write_configs()
        self.create_pipeline()
        self.cleanup

    def prepare_onetime_pipeline(self, onetime=None):
        self.write_configs()
        self.create_pipeline(onetime=onetime)
        self.cleanup()

if __name__ == "__main__":
    #foremastrunner = ForemastRunner(group="forrest", repo="edge", env='dev')
    foremastrunner = ForemastRunner(group="forrest", repo="edge")
    foremastrunner.prepare_onetime_pipeline(onetime='dev')
    

    

