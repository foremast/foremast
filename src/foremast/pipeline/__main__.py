"""Create Spinnaker Pipeline."""
import argparse
import logging

from ..args import add_app, add_debug, add_gitlab_token, add_properties, add_env
from ..consts import LOGGING_FORMAT, ENVS
from .create_pipeline import SpinnakerPipeline
from .create_pipeline_onetime import SpinnakerPipelineOnetime


def main():
    """Run newer stuffs."""
    logging.basicConfig(format=LOGGING_FORMAT)
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    add_debug(parser)
    add_app(parser)
    add_properties(parser)
    add_gitlab_token(parser)
    parser.add_argument('-b',
                        '--base',
                        help='Base AMI name to use, e.g. fedora, tomcat')
    parser.add_argument(
        "--triggerjob",
        help="The jenkins job to monitor for pipeline triggering",
        required=True)
    parser.add_argument(
        "--onetime",
        required=False,
        choices=ENVS,
        help='Onetime deployment environment')
    args = parser.parse_args()
    print(args)

    if args.base and '"' in args.base:
        args.base = args.base.strip('"')

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    log.debug('Parsed arguments: %s', args)

    if args.onetime:
        spinnakerapps = SpinnakerPipelineOnetime(app_info=vars(args))
        spinnakerapps.create_pipeline()
    else:
        spinnakerapps = SpinnakerPipeline(app_info=vars(args))
        spinnakerapps.create_pipeline()


if __name__ == "__main__":
    main()
