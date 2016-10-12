#   Foremast - Pipeline Tooling
#
#   Copyright 2016 Gogo, LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""CLI entrypoint to Application Configuration preparer.

Help: ``python -m src.foremast.configs -h``
"""
import argparse
import logging

import gogoutils

from ..args import add_debug
from ..consts import APP_FORMATS, LOGGING_FORMAT
from .outputs import write_variables
from .prepare_configs import process_git_configs, process_runway_configs

LOG = logging.getLogger(__name__)


def main():
    """Append Application Configurations to a given file in multiple formats."""
    logging.basicConfig(format=LOGGING_FORMAT)

    parser = argparse.ArgumentParser(description=main.__doc__)
    add_debug(parser)
    parser.add_argument('-o',
                        '--output',
                        required=True,
                        help='Name of environment file to append to')
    parser.add_argument(
        '-g',
        '--git-short',
        metavar='GROUP/PROJECT',
        required=True,
        help='Short name for Git, e.g. forrest/core')
    parser.add_argument(
        '-r',
        '--runway-dir',
        help='Runway directory with app.json files, requires --git-short')
    args = parser.parse_args()

    LOG.setLevel(args.debug)
    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    generated = gogoutils.Generator(
        *gogoutils.Parser(args.git_short).parse_url(), formats=APP_FORMATS)
    git_short = generated.gitlab()['main']

    if args.runway_dir:
        configs = process_runway_configs(runway_dir=args.runway_dir)
    else:
        configs = process_git_configs(git_short=git_short)

    write_variables(app_configs=configs,
                    out_file=args.output,
                    git_short=git_short)


if __name__ == '__main__':
    main()
