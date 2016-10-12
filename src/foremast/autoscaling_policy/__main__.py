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

"""Deletes existing scaling policy on application and then creates
new Autoscaling Policy based on provided configurations

Help: ```python -m src.foremast.autoscaling_policy -h```
"""
import argparse
import logging

from ..args import add_app, add_debug, add_env, add_properties, add_region
from ..consts import LOGGING_FORMAT
from .create_policy import AutoScalingPolicy


def main():
    """CLI entrypoint for scaling policy creation"""
    logging.basicConfig(format=LOGGING_FORMAT)
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    add_debug(parser)
    add_app(parser)
    add_properties(parser)
    add_env(parser)
    add_region(parser)
    args = parser.parse_args()

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    log.debug('Parsed arguments: %s', args)

    asgpolicy = AutoScalingPolicy(app=args.app,
                                  prop_path=args.properties,
                                  env=args.env,
                                  region=args.region)

    asgpolicy.create_policy()


if __name__ == "__main__":
    main()
