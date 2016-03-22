import requests
import argparse
import json
import logging
import sys
import os
from jinja2 import Template


class SpinnakerELB:

    def __init__(self):
        self.curdir = os.path.dirname(os.path.realpath(__file__))
        self.templatedir = "{}/../../templates".format(self.curdir)
        with open(self.templatedir + '/elb_data_template.json', 'r') as self.elb_json_file:
            self.elb_json = self.elb_json_file.read()
        self.gate_url = "http://spinnaker.build.example.com:8084"
        self.header = {'Content-Type': 'application/json', 'Accept': '*/*'}

    def get_vpc_id(self, account):
        url = self.gate_url + "/vpcs"
        response = requests.get(url)
        if response.ok:
            for vpc in response.json():
                if vpc['name'] == 'vpc' and vpc['account'] == account:
                    return vpc['id']
        else:
            logging.error(response.text)
            sys.exit(1)

    def create_elb(self, json_data, app):
        url = self.gate_url + '/applications/%s/tasks' %app
        response = requests.post(url, data=json.dumps(json_data), headers=self.header)
        print response.text


#python create_elb.py --app testapp --stack teststack --elb_type internal --env prod,stage --health_protocol HTTP --health_port 80 --health_path /health --security_groups sg_apps,sg_offices --int_listener_port 80 --int_listener_protocol HTTP --ext_listener_port 8080 --ext_listener_protocol HTTP --elb_name test_elb --elb_subnet internal --health_timeout=10 --health_interval=2 --healthy_threshold=4 --unhealthy_threshold=6

#python create_elb.py --app testapp --stack teststack --elb_type internal --env stage --health_protocol HTTP --health_port 80 --health_path /health --security_groups sg_apps --int_listener_port 80 --int_listener_protocol HTTP --ext_listener_port 8080 --ext_listener_protocol HTTP --elb_name dougtestapp-teststack --elb_subnet internal --health_timeout=10 --health_interval 2 --healthy_threshold 4 --unhealthy_threshold 6
if __name__ == '__main__':
    elb = SpinnakerELB()
    parser = argparse.ArgumentParser(description='Example with non-optional arguments')

    parser.add_argument('--app', action="store", help="application name", required=True)
    parser.add_argument('--stack', action="store", help="application stack", required=True)
    parser.add_argument('--elb_type', action="store", help="elb type: internal/external", required=True)
    parser.add_argument('--env', action="store", help="environment: dev, stage, prod", required=True)
    parser.add_argument('--health_protocol', action="store", help="health check protocol: http/tcp", required=True)
    parser.add_argument('--health_port', action="store", help="health check port", required=True)
    parser.add_argument('--health_path', action="store", help="health check path stack", required=False, default="/health")
    parser.add_argument('--health_timeout', action="store", help="health check timeout in seconds", required=True, default=10)
    parser.add_argument('--health_interval', action="store", help="health check interval in seconds", required=True, default=20)
    parser.add_argument('--healthy_threshold', action="store", help="healthy threshold", required=True, default=2)
    parser.add_argument('--unhealthy_threshold', action="store", help="unhealthy threshold", required=True, default=5)
    parser.add_argument('--security_groups', action="store", help="security groups", required=True, default="sg_apps", nargs="+")
    parser.add_argument('--int_listener_port', action="store", help="internal listener port", required=True, default=8080)
    parser.add_argument('--int_listener_protocol', action="store", help="internal listener protocol", required=True, default="HTTP")
    parser.add_argument('--ext_listener_port', action="store", help="internal listener port", required=True, default=80)
    parser.add_argument('--ext_listener_protocol', action="store", help="external listener protocol", required=True, default="HTTP")
    parser.add_argument('--elb_name', action="store", help="elb name", required=True)
    parser.add_argument('--elb_subnet', action="store", help="elb subnet", required=True, default="internal")
    args = parser.parse_args()
    template = Template(elb.elb_json).render(app_stack=args.stack,
                                            app_name=args.app,
                                            env=args.env,
                                            isInternal='true' if args.elb_type == 'internal' else 'false',
                                            vpc_id=elb.get_vpc_id(args.env),
                                            health_protocol=args.health_protocol,
                                            health_port=args.health_port,
                                            health_path=args.health_path,
                                            health_timeout=args.health_timeout,
                                            health_interval=args.health_interval,
                                            unhealthy_threshold=args.unhealthy_threshold,
                                            healthy_threshold=args.healthy_threshold,
                                            security_groups=args.security_groups[0],
                                            int_listener_protocol=args.int_listener_protocol,
                                            ext_listener_protocol=args.ext_listener_protocol,
                                            int_listener_port=args.int_listener_port,
                                            ext_listener_port=args.ext_listener_port,
                                            elb_name=args.elb_name,
                                            subnet_type=args.elb_subnet,
                                            elb_subnet=args.elb_subnet,
                                            hc_string='HTTP:80/health')
    blah = json.loads(template)
    elb.create_elb(json.dumps(blah), args.app)





