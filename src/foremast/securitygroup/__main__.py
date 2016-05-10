"""Create Security Group."""
import argparse
import logging

from ..args import add_app, add_debug, add_env, add_properties
from ..consts import LOGGING_FORMAT
from .create_securitygroup import SpinnakerSecurityGroup


def main():
    """Run newer stuffs."""
    logging.basicConfig(format=LOGGING_FORMAT)
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    add_debug(parser)
    add_app(parser)
    add_env(parser)
    add_properties(parser)
    parser.add_argument("--region",
                        help="The region to create the security group",
                        required=True)
    args = parser.parse_args()

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    log.debug('Parsed arguments: %s', args)

    spinnakerapps = SpinnakerSecurityGroup(args)
    spinnakerapps.create_security_group()


if __name__ == "__main__":
    main()
