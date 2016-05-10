"""Destroy IAM command."""
import argparse
import logging

from ...args import add_app, add_debug, add_env
from ...consts import LOGGING_FORMAT
from .destroy_iam import destroy_iam

LOG = logging.getLogger(__name__)


def main():
    """Destroy any IAM related Resources."""
    logging.basicConfig(format=LOGGING_FORMAT)

    parser = argparse.ArgumentParser(description=main.__doc__)
    add_debug(parser)
    add_app(parser)
    add_env(parser)
    args = parser.parse_args()

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    destroy_iam(**vars(args))


if __name__ == '__main__':
    main()
