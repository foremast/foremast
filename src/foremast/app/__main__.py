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

"""CLI entry point for creating a Spinnaker application.

Help: ``python -m src.foremast.app -h``
"""
import argparse
import logging

import gogoutils

from ..args import add_app, add_debug
from ..consts import LOGGING_FORMAT, APP_FORMATS
from .create_app import SpinnakerApp


def main():
    """Entry point for creating a Spinnaker application."""
    # Setup parser
    parser = argparse.ArgumentParser()
    add_debug(parser)
    add_app(parser)
    parser.add_argument('--email',
                        help='Email address to associate with application',
                        default='PS-DevOpsTooling@example.com')
    parser.add_argument('--project',
                        help='Git project to associate with application',
                        default='None')
    parser.add_argument('--repo',
                        help='Git repo to associate with application',
                        default='None')
    parser.add_argument('--git', help='Git URI', default=None)
    args = parser.parse_args()

    logging.basicConfig(format=LOGGING_FORMAT)
    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    if args.git and args.git != 'None':
        parsed = gogoutils.Parser(args.git).parse_url()
        generated = gogoutils.Generator(*parsed, formats=APP_FORMATS)
        project = generated.project
        repo = generated.repo
    else:
        project = args.project
        repo = args.repo

    spinnakerapps = SpinnakerApp(app=args.app,
                                 email=args.email,
                                 project=project,
                                 repo=repo)
    spinnakerapps.create_app()


if __name__ == '__main__':
    main()
