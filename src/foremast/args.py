"""Common _argparse_ arguments."""
import logging
from .consts import ENVS


def add_debug(parser):
    """Add a `debug` flag to the _parser_."""
    parser.add_argument('-d',
                        '--debug',
                        action='store_const',
                        const=logging.DEBUG,
                        default=logging.INFO,
                        help='Set DEBUG output')


def add_env(parser):
    """Add an `env` flag to the _parser_."""
    parser.add_argument('-e',
                        '--env',
                        choices=ENVS,
                        default='dev',
                        help='Deploy environment')


def add_app(parser):
    """Add an `app` flag to the _parser_."""
    parser.add_argument('-a',
                        '--app',
                        help='Spinnaker Application name',
                        required=True)


def add_properties(parser):
    """Add a `settings` flag to the _parser_."""
    parser.add_argument(
        '-p',
        '--properties',
        help='Location of JSON file produced by *create-configs*',
        default="./raw.properties.json")


def add_region(parser):
    """Add a `region` flag to the _parser_."""
    parser.add_argument('-r',
                        '--region',
                        default='us-east-1',
                        help='Region to create Resources in, e.g. us-east-1')
