"""Create Spinnaker Application."""
import argparse
import logging

import gogoutils

from ..args import add_debug
from ..consts import LOGGING_FORMAT
from .create_app import SpinnakerApp


def main():
    """Create Spinnaker Application."""
    # Setup parser
    parser = argparse.ArgumentParser()
    add_debug(parser)
    parser.add_argument("--app", help="The application name to create",
                        required=True)
    parser.add_argument("--email", help="Email address to associate with application",
                        default="PS-DevOpsTooling@example.com")
    parser.add_argument("--project", help="The project to associate with application",
                        default="None")
    parser.add_argument("--repo", help="The repo to associate with application",
                        default="None")
    parser.add_argument("--git", help="Git URI", default=None)
    args = parser.parse_args()

    logging.basicConfig(format=LOGGING_FORMAT)
    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    if args.git and args.git != 'None':
        generated = gogoutils.Generator(*gogoutils.Parser(args.git).parse_url())
        project = generated.project
        repo = generated.repo
    else:
        project = args.project
        repo = args.repo

    appinfo = {
        "app": args.app,
        "email": args.email,
        "project": project,
        "repo": repo
    }

    spinnakerapps = SpinnakerApp(appinfo=appinfo)
    spinnakerapps.create_app()


if __name__ == "__main__":
    main()
