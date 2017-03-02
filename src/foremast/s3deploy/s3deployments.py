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

import logging

import boto3

from ..utils import get_properties

LOG = logging.getLogger(__name__)

class S3Deployments(object):
    """Handles infrastructure around depolying static content to S3"""

    def __init__(self, app, env, region, prop_path):
        self.app_name = app
        self.env = env
        self.region = region
        self.properties = get_properties(prop_path)
        boto_sess = boto3.session.Session(profile_name=env)
        self.s3client = boto_sess.client('s3')

    def create_bucket(self):
        print("TEST")
