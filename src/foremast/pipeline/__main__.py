"""CLI entry point to create Spinnaker Pipelines.

Help: ``python -m src.foremast.pipeline -h``
"""
import argparse
import logging

from ..args import add_app, add_debug, add_gitlab_token, add_properties
from ..consts import ENVS, LOGGING_FORMAT
from .create_pipeline import SpinnakerPipeline
from .create_pipeline_onetime import SpinnakerPipelineOnetime


def main():
    """Creates a pipeline in Spinnaker"""
    logging.basicConfig(format=LOGGING_FORMAT)
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    add_debug(parser)
    add_app(parser)
    add_properties(parser)
    parser.add_argument('-b',
                        '--base',
                        help='Base AMI name to use, e.g. fedora, tomcat')
    parser.add_argument(
        "--triggerjob",
        help="The jenkins job to monitor for pipeline triggering",
        required=True)
    parser.add_argument('--onetime',
                        required=False,
                        choices=ENVS,
                        help='Onetime deployment environment')
    args = parser.parse_args()

    if args.base and '"' in args.base:
        args.base = args.base.strip('"')

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    log.debug('Parsed arguments: %s', args)

    if args.onetime:
        spinnakerapps = SpinnakerPipelineOnetime(app=args.app,
                                                 onetime=args.onetime,
                                                 trigger_job=args.triggerjob,
                                                 prop_path=args.properties,
                                                 base=args.base)
        spinnakerapps.create_pipeline()
    else:
        spinnakerapps = SpinnakerPipeline(app=args.app,
                                          trigger_job=args.triggerjob,
                                          prop_path=args.properties,
                                          base=args.base)
        spinnakerapps.create_pipeline()


if __name__ == "__main__":
    main()
