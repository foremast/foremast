"""Create Spinnaker Pipeline."""
import argparse
import logging

from ..args import add_debug
from ..consts import LOGGING_FORMAT
from .create_pipeline import SpinnakerPipeline


def main():
    """Run newer stuffs."""
    logging.basicConfig(format=LOGGING_FORMAT)
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    add_debug(parser)
    parser.add_argument("--app",
                        help="The application name to create",
                        required=True)
    parser.add_argument(
        "--triggerjob",
        help="The jenkins job to monitor for pipeline triggering",
        required=True)
    parser.add_argument(
        "--properties",
        help="Location of json file that contains application.json details",
        default="./raw.properties.json",
        required=False)
    # parser.add_argument("--vpc",
    #                     help="The vpc to create the security group",
    #                     required=True)
    args = parser.parse_args()

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    log.debug('Parsed arguments: %s', args)

    # Dictionary containing application info. This is passed to the class for
    # processing
    appinfo = {
        'app': args.app,
        # 'vpc': args.vpc,
        'triggerjob': args.triggerjob,
        'properties': args.properties
    }

    spinnakerapps = SpinnakerPipeline(app_info=appinfo)
    spinnakerapps.create_pipeline()


if __name__ == "__main__":
    main()
