"""ELB creation."""
import argparse
import logging

from ..args import add_debug, add_properties
from ..consts import LOGGING_FORMAT
from .create_elb import SpinnakerELB

LOG = logging.getLogger(__name__)


def main():
    """Create ELBs.

    python create_elb.py \
        --app testapp \
        --stack teststack \
        --elb-type internal \
        --env dev \
        --health-protocol HTTP \
        --health-port 80 \
        --health-path /health \
        --security-groups apps-all \
        --int-listener-port 80 \
        --int-listener-protocol HTTP \
        --ext-listener-port 8080 \
        --ext-listener-protocol HTTP \
        --elb-name dougtestapp-teststack \
        --elb-subnet internal \
        --health-timeout=10 \
        --health-interval 2 \
        --healthy-threshold 4 \
        --unhealthy-threshold 6 \
        --region us-east-1
    """
    logging.basicConfig(format=LOGGING_FORMAT)

    parser = argparse.ArgumentParser(
        description='Example with non-optional arguments')

    add_debug(parser)
    add_properties(parser)
    parser.add_argument('--app', action="store", help="application name", required=True)
    parser.add_argument('--env', action="store", help="environment: dev, stage, prod", required=True)
    parser.add_argument('--health-target', action="store", help="Target for Health Check, e.g. HTTP:80/health", required=True)
    parser.add_argument('--health-timeout', action="store", help="health check timeout in seconds", default=10)
    parser.add_argument('--health-interval', action="store", help="health check interval in seconds", default=20)
    parser.add_argument('--healthy-threshold', action="store", help="healthy threshold", default=2)
    parser.add_argument('--unhealthy-threshold', action="store", help="unhealthy threshold", default=5)
    parser.add_argument('--security-groups', action="store", help="security groups", default="sg_apps", nargs="+")
    # parser.add_argument('--elb-name', action="store", help="elb name", required=True)
    parser.add_argument('--subnet-xxxx', action="store", help="ELB Subnet type, e.g. external, internal", default="internal")
    parser.add_argument('--region', help="region name", default="us-east-1")

    args = parser.parse_args()

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    elb = SpinnakerELB(args)
    elb.create_elb()


if __name__ == '__main__':
    main()
