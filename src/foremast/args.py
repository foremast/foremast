"""Common _argparse_ arguments."""
import logging


def add_debug(parser):
    """Add a `debug` flag to the _parser_."""
    parser.add_argument('-d',
                        '--debug',
                        action='store_const',
                        const=logging.DEBUG,
                        default=logging.INFO,
                        help='Set DEBUG output')


def add_properties(parser):
    """Add a `settings` flag to the _parser_."""
    parser.add_argument(
        '-p',
        '--properties',
        help='Location of JSON file produced by *create-configs*',
        default="./raw.properties.json")
