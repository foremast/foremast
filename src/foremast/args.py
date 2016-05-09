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


def add_env(parser):
    """Add an `env` flag to the _parser_."""
    parser.add_argument(
        '-e',
        '--env',
        choices=('build', 'dev', 'stage', 'prod', 'prods', 'prodp'),
        default='dev',
        help='Deploy environment')


def add_app(parser):
    """Add an `app` flag to the _parser_."""
    parser.add_argument('-a',
                        '--app',
                        default='testapp',
                        help='Spinnaker Application name')


def add_properties(parser):
    """Add a `settings` flag to the _parser_."""
    parser.add_argument(
        '-p',
        '--properties',
        help='Location of JSON file produced by *create-configs*',
        default="./raw.properties.json")
