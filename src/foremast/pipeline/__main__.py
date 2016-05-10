"""Create Spinnaker Pipeline."""
import argparse
import logging

from ..args import add_app, add_debug, add_properties
from ..consts import LOGGING_FORMAT
from .create_pipeline import SpinnakerPipeline


def main():
    """Run newer stuffs."""
    logging.basicConfig(format=LOGGING_FORMAT)
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    add_debug(parser)
    add_app(parser)
    add_properties(parser)
    parser.add_argument('-b',
                        '--base',
                        help='Base AMI name to use, e.g. fedora, tomcat')
    parser.add_argument('-t',
                        '--token-file',
                        help='File with GitLab API private token',
                        default='~/.aws/git.token')
    parser.add_argument(
        "--triggerjob",
        help="The jenkins job to monitor for pipeline triggering",
        required=True)
    args = parser.parse_args()

    if args.base and '"' in args.base:
        args.base = args.base.strip('"')

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    log.debug('Parsed arguments: %s', args)

    spinnakerapps = SpinnakerPipeline(app_info=vars(args))
    spinnakerapps.create_pipeline()


if __name__ == "__main__":
    main()
