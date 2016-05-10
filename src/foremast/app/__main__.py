"""Create Spinnaker Application."""
import argparse
import logging

import gogoutils

from ..args import add_app, add_debug
from ..consts import LOGGING_FORMAT
from .create_app import SpinnakerApp


def main():
    """Create Spinnaker Application."""
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
        generated = gogoutils.Generator(*parsed)
        project = generated.project
        repo = generated.repo
    else:
        project = args.project
        repo = args.repo

    appinfo = {
        'app': args.app,
        'email': args.email,
        'project': project,
        'repo': repo
    }

    spinnakerapps = SpinnakerApp(appinfo=appinfo)
    spinnakerapps.create_app()


if __name__ == '__main__':
    main()
