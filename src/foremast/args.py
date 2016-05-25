"""Common _argparse_ arguments."""
import logging

from .consts import ENVS


def add_app(parser):
    """Add an `app` flag to the _parser_."""
    parser.add_argument('-a',
                        '--app',
                        help='Spinnaker Application name',
                        required=True)


def add_debug(parser):
    """Add a `debug` flag to the _parser_."""
    parser.add_argument('-d',
                        '--debug',
                        action='store_const',
                        const=logging.DEBUG,
                        default=logging.INFO,
                        help='Set DEBUG output')


def add_env(parser, env_default='dev'):
    """Add an `env` flag to the _parser_."""
    parser.add_argument('-e',
                        '--env',
                        choices=ENVS,
                        default=env_default,
                        help='Deploy environment')


def add_gitlab_token(parser):
    """Add a `token-file` flag to the _parser_."""
    parser.add_argument('-t',
                        '--token-file',
                        help='File with GitLab API private token',
                        default='~/.aws/git.token')


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
