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
    parser.add_argument('-b', '--base',
                        help='Base AMI name to use, e.g. fedora, tomcat',
                        default='tomcat')
    parser.add_argument(
        "--triggerjob",
        help="The jenkins job to monitor for pipeline triggering",
        required=True)
    parser.add_argument(
        "--properties",
        help="Location of json file that contains application.json details",
        default="./raw.properties.json",
        required=False)
    args = parser.parse_args()

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    log.debug('Parsed arguments: %s', args)

    spinnakerapps = SpinnakerPipeline(app_info=vars(args))
    spinnakerapps.create_pipeline()


if __name__ == "__main__":
    main()
