"""Foremast CLI commands."""
import argparse
import logging

from .args import add_debug
from .consts import LOGGING_FORMAT

LOG = logging.getLogger(__name__)


def main(manual_args=None):
    """Foremast, your ship's support."""
    logging.basicConfig(format=LOGGING_FORMAT)

    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.set_defaults(func=parser.print_help)
    add_debug(parser)

    args, args_list = parser.parse_known_args(args=manual_args)

    package, *_ = __package__.split('.')
    logging.getLogger(package).setLevel(args.debug)

    LOG.debug('Arguments: %s', args)
    LOG.debug('Leftover arguments: %s', args_list)

    try:
        args.func(args)
    except AttributeError:
        args.func()


if __name__ == '__main__':
    main()
