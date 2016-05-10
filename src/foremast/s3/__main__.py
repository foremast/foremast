"""Add application.properties to Application's S3 Bucket directory."""
import argparse
import logging

from ..args import add_app, add_debug, add_env
from ..consts import LOGGING_FORMAT
from .create_archaius import init_properties

LOG = logging.getLogger(__name__)


def main():
    """Create application.properties for a given application."""
    logging.basicConfig(format=LOGGING_FORMAT)

    parser = argparse.ArgumentParser(description=main.__doc__)

    add_debug(parser)
    add_app(parser)
    add_env(parser)

    args = parser.parse_args()

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)
    vars(args).pop('debug')

    LOG.debug('Args: %s', vars(args))

    init_properties(env=args.env, app=args.app)


if __name__ == '__main__':
    main()
