"""Create ELBs for Spinnaker Pipelines."""
import argparse
import json
import logging
import os
from exceptions import SpinnakerTaskError

import requests
from jinja2 import Environment, FileSystemLoader

from utils import check_task, get_subnets, get_vpc_id

LOG = logging.getLogger(__name__)


class SpinnakerELB:
    """Create ELBs for Spinnaker."""

    def __init__(self):
        self.curdir = os.path.dirname(os.path.realpath(__file__))
        self.templatedir = "{}/../../templates".format(self.curdir)
        jinjaenv = Environment(loader=FileSystemLoader(self.templatedir))
        self.elb_template = jinjaenv.get_template("elb_data_template.json")
        self.gate_url = "http://gate-api.build.example.com:8084"
        self.header = {'Content-Type': 'application/json', 'Accept': '*/*'}

    def create_elb(self, json_data, app):
        """Create/Update ELB.

        Args:
            json_data: elb json payload.
            app: application name related to this ELB.

        Returns:
            task id to track the elb creation status.
        """
        url = self.gate_url + '/applications/%s/tasks' % app
        response = requests.post(url,
                                 data=json.dumps(json_data),
                                 headers=self.header)
        if response.ok:
            LOG.info('%s ELB Created', app)
            LOG.info(response.text)
            return response.json()
        else:
            LOG.error('Error creating %s ELB:', app)
            LOG.error(response.text)
            return response.json()


def main():
    """Create ELBs.

    python create_elb.py \
        --app testapp \
        --stack teststack \
        --elb_type internal \
        --env dev \
        --health_protocol HTTP \
        --health_port 80 \
        --health_path /health \
        --security_groups sg_apps \
        --int_listener_port 80 \
        --int_listener_protocol HTTP \
        --ext_listener_port 8080 \
        --ext_listener_protocol HTTP \
        --elb_name dougtestapp-teststack \
        --elb_subnet internal \
        --health_timeout=10 \
        --health_interval 2 \
        --healthy_threshold 4 \
        --unhealthy_threshold 6 \
        --region us-east-1
    """
    logging.basicConfig(
        format=
        '[%(levelname)s]%(module)s:%(funcName)s:%(lineno)d - %(message)s')

    parser = argparse.ArgumentParser(
        description='Example with non-optional arguments')

    parser.add_argument('-d',
                        '--debug',
                        action='store_const',
                        const=logging.DEBUG,
                        default=logging.INFO,
                        help='Set DEBUG output')
    parser.add_argument('--app', action="store", help="application name", required=True)
    parser.add_argument('--env', action="store", help="environment: dev, stage, prod", required=True)
    parser.add_argument('--health-target', action="store", help="Target for Health Check, e.g. HTTP:80/health", required=True)
    parser.add_argument('--health-timeout', action="store", help="health check timeout in seconds", default=10)
    parser.add_argument('--health-interval', action="store", help="health check interval in seconds", default=20)
    parser.add_argument('--healthy-threshold', action="store", help="healthy threshold", default=2)
    parser.add_argument('--unhealthy-threshold', action="store", help="unhealthy threshold", default=5)
    parser.add_argument('--security-groups', action="store", help="security groups", default="sg_apps", nargs="+")
    parser.add_argument('--int-listener-port', action="store", help="internal listener port", default=8080)
    parser.add_argument('--int-listener-protocol', action="store", help="internal listener protocol", default="HTTP")
    parser.add_argument('--ext-listener-port', action="store", help="internal listener port", default=80)
    parser.add_argument('--ext-listener-protocol', action="store", help="external listener protocol", default="HTTP")
    # parser.add_argument('--elb_name', action="store", help="elb name", required=True)
    parser.add_argument('--subnet-xxxx', action="store", help="ELB Subnet type, e.g. external, internal", default="internal")
    parser.add_argument('--region', help="region name", default="us-east-1")

    args = parser.parse_args()

    LOG.setLevel(args.debug)

    elb = SpinnakerELB()

    health_proto, health_port_path = args.health_target.split(':')
    health_port, *health_path = health_port_path.split('/')

    if len(health_path) > 0:
        health_path = '/{0}'.format(health_path)
    else:
        health_path = '/healthcheck'

    raw_subnets = get_subnets()
    region_subnets = {args.region: raw_subnets[args.env][args.region]}

    template = elb.elb_template.render(
        app_name=args.app,
        env=args.env,
        isInternal='true' if args.subnet_type == 'internal' else 'false',
        vpc_id=get_vpc_id(args.env, args.region),
        health_protocol=health_proto,
        health_port=health_port,
        health_path=health_path,
        health_timeout=args.health_timeout,
        health_interval=args.health_interval,
        unhealthy_threshold=args.unhealthy_threshold,
        healthy_threshold=args.healthy_threshold,
        # FIXME: Use json.dumps(args.security_groups) to format for template
        security_groups=args.security_groups,
        int_listener_protocol=args.int_listener_protocol,
        ext_listener_protocol=args.ext_listener_protocol,
        int_listener_port=args.int_listener_port,
        ext_listener_port=args.ext_listener_port,
        subnet_type=args.subnet_type,
        region=args.region,
        hc_string=args.health_target,
        availability_zones=json.dumps(region_subnets),
        region_zones=json.dumps(region_subnets[args.region]),
    )

    LOG.info('Rendered template:\n%s', template)

    rendered_json = json.loads(template)
    taskid = elb.create_elb(rendered_json, args.app)

    try:
        check_task(taskid, args.app)
    except SpinnakerTaskError:
        LOG.error('Error upserting ELB, exiting ...')
        raise


if __name__ == '__main__':
    main()
