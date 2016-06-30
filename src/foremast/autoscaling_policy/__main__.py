"""Create Autoscaling Policy"""
import argparse
import logging

from ..args import add_app, add_debug, add_region, add_gitlab_token, add_properties, add_env
from ..consts import ENVS, LOGGING_FORMAT
from .create_policy import AutoScalingPolicy


def main():
    """Run newer stuffs."""
    logging.basicConfig(format=LOGGING_FORMAT)
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    add_debug(parser)
    add_app(parser)
    add_properties(parser)
    add_env(parser)
    add_region(parser)
    args = parser.parse_args()

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    log.debug('Parsed arguments: %s', args)

    asgpolicy = AutoScalingPolicy(app=args.app,
                                  prop_path=args.properties,
                                  env=args.env,
                                  region=args.region)

    asgpolicy.create_policy()


if __name__ == "__main__":
    main()
