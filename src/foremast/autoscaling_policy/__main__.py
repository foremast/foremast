"""Create Autoscaling Policy"""
import argparse
import logging

from ..args import add_app, add_debug, add_gitlab_token, add_properties, add_env
from ..consts import ENVS, LOGGING_FORMAT
from .create_policy import create_policy


def main():
    """Run newer stuffs."""
    logging.basicConfig(format=LOGGING_FORMAT)
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    add_debug(parser)
    add_app(parser)
    add_properties(parser)
    add_gitlab_token(parser)
    add_env(parser)
    args = parser.parse_args()

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    log.debug('Parsed arguments: %s', args)

    spinnakerapps = SpinnakerPipeline(app=args.app,
                                      trigger_job=args.triggerjob,
                                      prop_path=args.properties,
                                      base=args.base,
                                      token_file=args.token_file)


if __name__ == "__main__":
    main()
