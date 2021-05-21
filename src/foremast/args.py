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
"""Common _argparse_ arguments."""
import logging
import os

from .consts import ENVS


def add_app(parser):
    """Add an `app` flag to the _parser_."""
    parser.add_argument('-a', '--app', help='Spinnaker Application name', required=True)


def add_debug(parser):
    """Add a `debug` flag to the _parser_."""
    parser.add_argument(
        '-d', '--debug', action='store_const', const=logging.DEBUG, default=logging.INFO, help='Set DEBUG output')


def add_env(parser):
    """Add an `env` flag to the _parser_."""
    parser.add_argument(
        '-e', '--env', choices=ENVS, default=os.getenv('ENV', default='dev'), help='Deploy environment, overrides $ENV')


def add_gitlab_token(parser):
    """Add a `token-file` flag to the _parser_."""
    parser.add_argument('-t', '--token-file', help='File with GitLab API private token', default='~/.aws/git.token')


def add_properties(parser):
    """Add a `settings` flag to the _parser_."""
    parser.add_argument(
        '-p',
        '--properties',
        help='Location of JSON file produced by *create-configs*',
        default="./raw.properties.json")


def add_region(parser):
    """Add a `region` flag to the _parser_."""
    parser.add_argument('-r', '--region', default='us-east-1', help='Region to create Resources in, e.g. us-east-1')


def add_artifact_path(parser):
    """Add an `artifact-path` flag to _parser_."""
    parser.add_argument('--artifact-path', help='Local path to artifact directory for S3 deployments')


def add_artifact_version(parser):
    """Add an `artifact-version` flag to _parser_."""
    parser.add_argument('--artifact-version', help='Artifact version for S3 deployments')


def add_provider(parser):
    """Add an `provider` flag to _parser_."""
    parser.add_argument('--provider', help='Cloud provider name', default='aws')
