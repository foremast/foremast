"""Entrypoint to Application Configuration preparer."""
import argparse
import logging

import gogoutils

from ..args import add_debug, add_gitlab_token
from ..consts import LOGGING_FORMAT
from .outputs import write_variables
from .prepare_configs import process_git_configs, process_runway_configs

LOG = logging.getLogger(__name__)


def main():
    """Append Application Configurations to a given file in INI format."""
    logging.basicConfig(format=LOGGING_FORMAT)

    parser = argparse.ArgumentParser(description=main.__doc__)
    add_debug(parser)
    add_gitlab_token(parser)
    parser.add_argument('-o',
                        '--output',
                        required=True,
                        help='Name of environment file to append to')
    parser.add_argument(
        '-g',
        '--git-short',
        metavar='GROUP/PROJECT',
        required=True,
        help='Short name for Git, e.g. forrest/core, requires --token-file')
    parser.add_argument(
        '-r',
        '--runway-dir',
        help='Runway directory with app.json files, requires --git-short')
    args = parser.parse_args()

    LOG.setLevel(args.debug)
    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    generated = gogoutils.Generator(
        *gogoutils.Parser(args.git_short).parse_url())
    git_short = generated.gitlab()['main']

    if args.runway_dir:
        configs = process_runway_configs(runway_dir=args.runway_dir)
    else:
        configs = process_git_configs(git_short=git_short,
                                      token_file=args.token_file)

    write_variables(app_configs=configs,
                    out_file=args.output,
                    git_short=git_short)


if __name__ == '__main__':
    main()
