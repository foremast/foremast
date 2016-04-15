"""Create ELBs for Spinnaker Pipelines."""
import argparse
import json
import logging
import os
import sys

import requests
from jinja2 import Environment, FileSystemLoader
from tryagain import retries


class SpinnakerELB:
    """Create ELBs for Spinnaker."""

    def __init__(self):
        self.curdir = os.path.dirname(os.path.realpath(__file__))
        self.templatedir = "{}/../../templates".format(self.curdir)
        jinjaenv = Environment(loader=FileSystemLoader(self.templatedir))
        self.elb_template = jinjaenv.get_template("elb_data_template.json")
        self.gate_url = "http://gate-api.build.example.com:8084"
        self.header = {'Content-Type': 'application/json', 'Accept': '*/*'}

    def get_vpc_id(self, account):
        """Get vpc id.

        Args:
            account: AWS account name.

        Returns:
            vpc_id.
        """
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
            logging.info('%s ELB Created' % app)
            logging.info(response.text)
            return response.json()
        else:
            logging.error('Error creating %s ELB:' % app)
            logging.error(response.text)
            return response.json()

    @retries(max_attempts=10, wait=10, exceptions=Exception)
    def check_task(self, taskid, app_name):
        """Check ELB creation status.
        Args:
            taskid: the task id returned from create_elb.
            app_name: application name related to this task.

        Returns:
            polls for task status.
        """

        try:
            taskurl = taskid.get('ref', '0000')
        except AttributeError:
            taskurl = taskid

        taskid = taskurl.split('/tasks/')[-1]

        logging.info('Checking taskid %s' % taskid)

        url = '{0}/applications/{1}/tasks/{2}'.format(self.gate_url, app_name,
                                                      taskid)

        r = requests.get(url, headers=self.header)

        logging.debug(r.json())
        if not r.ok:
            raise Exception
        else:
            json = r.json()
            status = json['status']
            logging.info('Current task status: %s', status)
            STATUSES = ('SUCCEEDED', 'TERMINAL')

            if status in STATUSES:
                return status
            else:
                raise Exception


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
    elb = SpinnakerELB()

    parser = argparse.ArgumentParser(
        description='Example with non-optional arguments')

    parser.add_argument('--app', action="store", help="application name", required=True)
    parser.add_argument('--elb_type', action="store", help="elb type: internal/external", required=True)
    parser.add_argument('--env', action="store", help="environment: dev, stage, prod", required=True)
    parser.add_argument('--health_protocol', action="store", help="health check protocol: http/tcp", required=True)
    parser.add_argument('--health_port', action="store", help="health check port", required=True)
    parser.add_argument('--health_path', action="store", help="health check path", required=False, default="/health")
    parser.add_argument('--health_timeout', action="store", help="health check timeout in seconds", required=True, default=10)
    parser.add_argument('--health_interval', action="store", help="health check interval in seconds", required=True, default=20)
    parser.add_argument('--healthy_threshold', action="store", help="healthy threshold", required=True, default=2)
    parser.add_argument('--unhealthy_threshold', action="store", help="unhealthy threshold", required=True, default=5)
    parser.add_argument('--security_groups', action="store", help="security groups", required=True, default="sg_apps", nargs="+")
    parser.add_argument('--int_listener_port', action="store", help="internal listener port", required=True, default=8080)
    parser.add_argument('--int_listener_protocol', action="store", help="internal listener protocol", required=True, default="HTTP")
    parser.add_argument('--ext_listener_port', action="store", help="internal listener port", required=True, default=80)
    parser.add_argument('--ext_listener_protocol', action="store", help="external listener protocol", required=True, default="HTTP")
    # parser.add_argument('--elb_name', action="store", help="elb name", required=True)
    parser.add_argument('--elb_subnet', action="store", help="elb subnet", required=True, default="internal")
    parser.add_argument('--region', help="region name", required=True, default="us-east-1")
    args = parser.parse_args()
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

    template = elb.elb_template.render(
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
        # elb_name=args.elb_name,
        subnet_type=args.elb_subnet,
        elb_subnet=args.elb_subnet,
        region=args.region,
        hc_string=args.int_listener_protocol + ':' + str(
            args.int_listener_port) + args.health_path if args.health_protocol
        == 'HTTP' else args.health_protocol + ':' + str(
            args.int_listener_port))

    rendered_json = json.loads(template)
    logging.info(rendered_json)
    taskid = elb.create_elb(rendered_json, args.app)
    if elb.check_task(taskid, args.app) == "SUCCEEDED":
        logging.info("ELB upserted successfully.")
        sys.exit(0)
    else:
        logging.error("Error upserting ELB, exiting ...")
        sys.exit(1)


if __name__ == '__main__':
    main()
