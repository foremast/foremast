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
        --env dev \
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

    elb = SpinnakerELB(app=args.app, env=args.env, region=args.region,
                       prop_path=args.properties)
    elb.create_elb()


if __name__ == '__main__':
    main()
