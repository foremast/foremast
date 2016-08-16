"""Create API Gateway events and integration."""
import argparse
import logging

from ...args import add_app, add_debug, add_env, add_region, add_properties
from ...consts import LOGGING_FORMAT
from .api_gateway_event import APIGateway


def main():
    """Create any API Gateway event related resources."""
    logging.basicConfig(format=LOGGING_FORMAT)

    parser = argparse.ArgumentParser(description=main.__doc__)
    add_debug(parser)
    add_app(parser)
    add_env(parser)
    add_region(parser)
    add_properties(parser)
    args = parser.parse_args()

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    apigateway = APIGateway(**vars(args))
    apigateway.setup_lambda_api()


if __name__ == '__main__':
    main()
