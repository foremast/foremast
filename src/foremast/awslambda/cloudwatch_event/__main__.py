"""Create Cloudwatch events."""
import argparse
import logging

from ...args import add_app, add_debug, add_env, add_region
from ...consts import LOGGING_FORMAT
from .cloudwatch_event import create_cloudwatch_event


def main():
    """Create any Cloudwatch events related Resources."""
    logging.basicConfig(format=LOGGING_FORMAT)

    parser = argparse.ArgumentParser(description=main.__doc__)
    add_debug(parser)
    add_app(parser)
    add_env(parser)
    add_region(parser)
    args = parser.parse_args()

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    assert create_cloudwatch_event(**vars(args))


if __name__ == '__main__':
    main()
