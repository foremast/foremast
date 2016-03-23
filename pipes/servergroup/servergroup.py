#!/usr/bin/env python

''' Script for creating and modifying Spinnaker server groups '''

import argparse
import configparser
import logging
import json
import os
import sys

from tryagain import retries
from jinja2 import Environment, FileSystemLoader
import requests

class SpinnakerServerGroup:
    """ Manipulates Spinnaker Server Groups/Clusters """

    def __init__(self):
        logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
        self.log = logging.getLogger(__name__)

        config = configparser.ConfigParser()
        self.here = os.path.dirname(os.path.realpath(__file__))
        configpath = "{}/../../configs/spinnaker.conf".format(self.here)
        config.read(configpath)
        self.gate_url = config['spinnaker']['gate_url'] 
        self.header = {'content-type': 'application/json'}

    def get_template(self):
        templatedir = "{}/../../templates".format(self.here)
        jinjaenv = Environment(loader=FileSystemLoader(templatedir))
        template = jinjaenv.get_template("servergroup_template.json")
        rendered_json = json.loads(template.render(sginfo=self.sginfo).replace("'", '"'))
        return rendered_json

    @retries(max_attempts=30, wait=30.0, exceptions=Exception)
    def check_task(self, taskid):

        try:
            taskurl = taskid.get('ref', '0000')
        except AttributeError:
            taskurl = taskid

        taskid = taskurl.split('/tasks/')[-1]

        self.log.info('Checking taskid %s' % taskid)

        url = '{0}/applications/{1}/tasks/{2}'.format(
            self.gate_url,
            self.sginfo['appname'],
            taskid,
        )

        r = requests.get(url, headers=self.header)

        self.log.debug(r.json())
        if not r.ok:
            raise Exception
        else:
            json = r.json()

            status = json['status']

            self.log.info('Current task status: %s', status)
            STATUSES = ('SUCCEEDED', 'TERMINAL')

            if status in STATUSES:
                return status
            else:
                raise Exception


    def upsert_servergroup(self, sginfo=None):
        """Updates the server group 
        
        Args:
            sginfo: dictionary for template rendering
        """
        #setup class variables for processing
        self.sginfo = sginfo

        url = "{}/applications/{}/tasks".format(self.gate_url, self.sginfo['appname'])
        jsondata = self.get_template()
        r = requests.post(url, data=json.dumps(jsondata), headers=self.header)
        
        status = self.check_task(r.json())
        if status not in ('SUCCEEDED'):
            self.log.error("Failed to create server group: {}".format(r.text))
            sys.exit(1)

        self.log.info("Successfully created {} server group".format(self.sginfo['appname']))
        return


#python servergroup.py --appname dougtestapp --account dev --aminame a_forrest_core_v0.0.102_b102_ami-xxxx-02-26-04-44_010fc03119
if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument("--appname", help="The application name for the server group",
                        required=True)
    parser.add_argument("--stackname", help="The stack name for the server group",
                        default="")
    parser.add_argument("--account", help="The account to create the server group in",
                        required=True)
    parser.add_argument("--min_capacity", help="The minimum amount of instances in a server group",
                        type=int, default=1)
    parser.add_argument("--max_capacity", help="The maximum amount of instances in a server group",
                        type=int, default=1)
    parser.add_argument("--desired_capacity", help="The desired amount of instances in a server group",
                        type=int, default=1)
    parser.add_argument("--iamrole", help="The iamrole to associate with the server group",
                        default='app_default_profile')
    parser.add_argument("--keypair", help="The keypair for accessing instances in the server group")
    parser.add_argument("--subnet_type", help="The subnet type to associate with security group",
                        default='internal')
    parser.add_argument("--securitygroups", help="The security groups instances in the server group",
                        nargs='*', default=[ "sg_offices", "sg_apps" ])
    parser.add_argument("--elbs", help="The ELBs to associate with the server group",
            nargs='*', default=[])
    parser.add_argument("--aminame", help="The ami for instances in the server group",
                        required=True)
    parser.add_argument("--instancetype", help="The instance type to use",
                        default='t2.medium')
    parser.add_argument("--b64_userdata", help="The userdata for instances in server group",
                        default='')

    args = parser.parse_args()

    if not args.keypair:
        args.keypair = "{}_access".format(args.account)

    
    if len(args.elbs) == 0:
        healthchecktype = 'EC2'
    else:
        healthchecktype = 'ELB'
         
    sginfo = {
            "appname": args.appname,
            "stackname": args.stackname,
            "account": args.account,
            "min_capacity": args.min_capacity,
            "max_capacity": args.max_capacity,
            "desired_capacity": args.desired_capacity,
            "healthchecktype": healthchecktype,
            "iamrole": args.iamrole,
            "subnet_type": args.subnet_type,
            "keypair": args.keypair,
            "securitygroups": args.securitygroups,
            "aminame": args.aminame,
            "elbs": [args.appname],
            "instancetype": args.instancetype,
            "b64_userdata": args.b64_userdata
            }

    sg = SpinnakerServerGroup()
    sg.upsert_servergroup(sginfo=sginfo)
