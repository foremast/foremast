"""CLI entry point for aws events creation.

Help: ``python -m src.foremast.awslambdaevent -h``
"""
import argparse
import logging

from ..args import add_app, add_debug, add_env, add_properties, add_region
from ..consts import LOGGING_FORMAT
from .awslambdaevent import LambdaEvent
from .awslambda import LambdaFunction


def main():
    """Create Lambda events."""
    logging.basicConfig(format=LOGGING_FORMAT)
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description=main.__doc__)
    add_debug(parser)
    add_app(parser)
    add_env(parser)
    add_properties(parser)
    add_region(parser)
    args = parser.parse_args()

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    log.debug('Parsed arguments: %s', args)

    lambda_function = LambdaFunction(app=args.app,
                                     env=args.env,
                                     region=args.region,
                                     prop_path=args.properties)

    lambda_function.create_lambda_function()

    lambda_event = LambdaEvent(app=args.app,
                               env=args.env,
                               region=args.region,
                               prop_path=args.properties)
    lambda_event.create_lambda_events()

if __name__ == "__main__":
    main()
