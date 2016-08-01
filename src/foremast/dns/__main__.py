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

"""CLI entry point for creating DNS record.

Help: ``python -m src.foremast.dns -h``
"""
import argparse
import logging

from ..args import add_app, add_debug, add_env, add_region, add_properties
from ..consts import LOGGING_FORMAT
from .create_dns import SpinnakerDns


def main():
    """Run newer stuffs."""
    logging.basicConfig(format=LOGGING_FORMAT)
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    add_debug(parser)
    add_app(parser)
    add_env(parser)
    add_region(parser)
    add_properties(parser)
    parser.add_argument("--elb-subnet",
                        help="Subnetnet type, e.g. external, internal",
                        required=True)
    args = parser.parse_args()

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    log.debug('Parsed arguments: %s', args)

    spinnakerapps = SpinnakerDns(app=args.app,
                                 env=args.env,
                                 region=args.region,
                                 prop_path=args.properties,
                                 elb_subnet=args.elb_subnet)
    spinnakerapps.create_elb_dns()


if __name__ == "__main__":
    main()
