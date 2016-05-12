"""ELB creation."""
import argparse
import logging

from ..args import add_app, add_debug, add_env, add_properties, add_region
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
    add_app(parser)
    add_env(parser)
    add_region(parser)
    add_properties(parser)

    args = parser.parse_args()

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    elb = SpinnakerELB(args)
    elb.create_elb()


if __name__ == '__main__':
    main()
