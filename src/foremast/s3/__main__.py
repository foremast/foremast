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
"""Add application.properties to Application's S3 Bucket directory.

Help: ``python -m src.foremast.s3 -h``
"""

import argparse
import logging

from ..args import add_app, add_artifact_path, add_artifact_version, add_debug, add_env, add_properties, add_region
from ..consts import LOGGING_FORMAT
from ..utils import get_properties
from .create_archaius import init_properties
from .s3apps import S3Apps
from .s3deploy import S3Deployment

LOG = logging.getLogger(__name__)


def main():
    """Create application.properties for a given application."""
    logging.basicConfig(format=LOGGING_FORMAT)

    parser = argparse.ArgumentParser(description=main.__doc__)

    add_debug(parser)
    add_app(parser)
    add_env(parser)
    add_properties(parser)
    add_region(parser)
    add_artifact_path(parser)
    add_artifact_version(parser)

    args = parser.parse_args()

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    LOG.debug('Args: %s', vars(args))

    rendered_props = get_properties(args.properties)
    if rendered_props['pipeline']['type'] == 's3':
        s3app = S3Apps(app=args.app, env=args.env, region=args.region, prop_path=args.properties)
        s3app.create_bucket()

        s3deploy = S3Deployment(
            app=args.app,
            env=args.env,
            region=args.region,
            prop_path=args.properties,
            artifact_path=args.artifact_path,
            artifact_version=args.artifact_version)
        s3deploy.upload_artifacts()
    else:
        init_properties(**vars(args))


if __name__ == '__main__':
    main()
