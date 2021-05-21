#   Foremast - Pipeline Tooling
#
#   Copyright 2018 Gogo, LLC
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
"""CLI entry point to create Spinnaker Pipelines.

Help: ``python -m src.foremast.pipeline -h``
"""
import argparse
import logging

from ..args import add_app, add_debug, add_properties
from ..consts import ENVS, LOGGING_FORMAT
from .create_pipeline import SpinnakerPipeline
from .create_pipeline_lambda import SpinnakerPipelineLambda
from .create_pipeline_cloudfunction import SpinnakerPipelineCloudFunction
from .create_pipeline_onetime import SpinnakerPipelineOnetime
from .create_pipeline_s3 import SpinnakerPipelineS3


def main():
    """Creates a pipeline in Spinnaker"""
    logging.basicConfig(format=LOGGING_FORMAT)
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    add_debug(parser)
    add_app(parser)
    add_properties(parser)
    parser.add_argument('-b', '--base', help='Base AMI name to use, e.g. fedora, tomcat')
    parser.add_argument("--triggerjob", help="The jenkins job to monitor for pipeline triggering", required=True)
    parser.add_argument('--onetime', required=False, choices=ENVS, help='Onetime deployment environment')
    parser.add_argument(
        '-t', '--type', dest='type', required=False, default='ec2', help='Deployment type, e.g. ec2, lambda')
    args = parser.parse_args()

    if args.base and '"' in args.base:
        args.base = args.base.strip('"')

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    log.debug('Parsed arguments: %s', args)

    if args.onetime:
        spinnakerapps = SpinnakerPipelineOnetime(
            app=args.app, onetime=args.onetime, trigger_job=args.triggerjob, prop_path=args.properties, base=args.base)
        spinnakerapps.create_pipeline()
    else:

        if args.type == "ec2":
            spinnakerapps = SpinnakerPipeline(
                app=args.app, trigger_job=args.triggerjob, prop_path=args.properties, base=args.base)
            spinnakerapps.create_pipeline()
        elif args.type == "lambda":
            spinnakerapps = SpinnakerPipelineLambda(
                app=args.app, trigger_job=args.triggerjob, prop_path=args.properties, base=args.base)
            spinnakerapps.create_pipeline()
        elif args.type == "s3":
            spinnakerapps = SpinnakerPipelineS3(
                app=args.app, trigger_job=args.triggerjob, prop_path=args.properties, base=args.base)
            spinnakerapps.create_pipeline()
        elif args.type == "cloudfunction":
            spinnakerapps = SpinnakerPipelineCloudFunction(
                app=args.app, trigger_job=args.triggerjob, prop_path=args.properties, base=args.base)
            spinnakerapps.create_pipeline()


if __name__ == "__main__":
    main()
