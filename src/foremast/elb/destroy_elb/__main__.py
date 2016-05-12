"""ELB cleanup."""
import argparse
import logging

from ...args import add_app, add_debug, add_env, add_region
from ...consts import LOGGING_FORMAT
from .destroy_elb import destroy_elb

LOG = logging.getLogger(__name__)


def main():
    """Destroy any ELB related Resources."""
    logging.basicConfig(format=LOGGING_FORMAT)

    parser = argparse.ArgumentParser(description=main.__doc__)
    add_debug(parser)
    add_app(parser)
    add_env(parser)
    add_region(parser)
    args = parser.parse_args()

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    assert destroy_elb(**vars(args))


if __name__ == '__main__':
    main()
