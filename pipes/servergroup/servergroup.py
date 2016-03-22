#!/usr/bin/env python

''' Script for creating and modifying Spinnaker server groups '''

import argparse
import configparser
import logging
import os
import sys

from jinja2 import Environment, FileSystemLoader
import requests

class ServerGroup:

    def __init__(self):
        config = configparser.ConfigParser()
        self.here = os.path.dirname(os.path.realpath(__file__))
        configpath = "{}/../../configs/spinnaker.conf".format(self.here)
        config.read(configpath)
        self.gate_url = config['spinnaker']['gate_url'] 

    def setup_sgdata(self):
        templatedir = "{}/../../templates".format(self.here)
        jinjaenv = Environment(loader=FileSystemLoader(templatedir))
        template = jinjaenv.get_template("app_data_template.json")
        rendered_json = json.loads(template.render(sginfo=self.sginfo))
        return rendered_json

    def upsert_servergroup(sginfo=None):
        #setup class variables for processing
        self.sginfo = sginfo

        url = "{}/applications/{}/tasks".format(self.gate_url, self.sginfo['appname'])
        jsondata = self.setup_sgdata()
        response = requests.post(url, data=json.dumps(jsondata), headers=self.header)
        
        if not response.ok:
            logging.error("Failed to create server group: {}".format(r.text))
            sys.exit(1)

        logging.info("Successfully created {} server group".format(self.appname))
        return


def keypair_name(account=None):
    keypair = "{}-access".format(account)
    return ke

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--appname", help="The application name for the server group",
                        required=True)
    parser.add_argument("--account", help="The account to create the server group in",
                        required=True)
    parser.add_argument("--min_capacity", help="The minimum amount of instances in a server group",
                        type=int, default=1)
    parser.add_argument("--max_capacity", help="The maximum amount of instances in a server group",
                        type=int, default=1)
    parser.add_argument("--desired_capacity", help="The desired amount of instances in a server group",
                        type=int, default=1)
    parser.add_argument("--iamrole", help="The iamrole to associate with the server group",
                        default='app_default_role')
    parser.add_argument("--keypair", help="The keypair for accessing instances in the server group")
    parser.add_argument("--securitygroups", help="The security groups instances in the server group")
    parser.add_argument("--aminame", help="The ami for instances in the server group",
                        required=True)
    parser.add_argument("--instancetype", help="The instance type to use",
                        default='t2.medium')
    parser.add_argument("--b64_userdata", help="The userdata for instances in server group",
                        default='')

    args = parser.parse_args()

    if not args.keypair:
        args.keypair = "{}-access".format(args.account)
        
    securitygroups = [ 'sg_apps' ]
    elbs = [ 'test' ]
    
    sginfo = {
            "appname": args.appname,
            "account": args.account,
            "min_capacity": args.min_capacity,
            "max_capacity": args.max_capacity,
            "desired_capacity": args.desired_capacity,
            "iamrole": args.iamrole,
            "keypair": args.keypair,
            "securitygroups": securitygroups,
            "aminame": args.aminame,
            "elbs": elbs,
            "instancetype": args.instancetype,
            "b64_userdata": args.b64_userdata,
            }

    sq = ServerGroup()
    sq.upsert_servergroup(sginfo=sginfo)
