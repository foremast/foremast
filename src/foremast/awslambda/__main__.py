"""CLI entry point for aws events creation

Help: ``python -m src.foremast.awslambdaevent -h``
"""
import argparse
import logging

from ..args import add_app, add_debug, add_env, add_properties, add_region
from ..consts import LOGGING_FORMAT
from .awslambdaevent import LambdaEvent


def main():
    """Entry point for creating an Lambda event"""
    logging.basicConfig(format=LOGGING_FORMAT)
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    add_debug(parser)
    add_app(parser)
    add_env(parser)
    add_properties(parser)
    add_region(parser)
    args = parser.parse_args()

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    log.debug('Parsed arguments: %s', args)

    lambdaevent = LambdaEvent(app=args.app,
                              env=args.env,
                              region=args.region,
                              prop_path=args.properties)
    lambdaevent.create_lambda_events()


if __name__ == "__main__":
    main()
