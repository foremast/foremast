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

"""Test IAM Policies for correctness."""
import json

from foremast.iam.construct_policy import construct_policy


def test_iam_construct_policy():
    """Check general assemblage."""
    settings = {}

    policy_json = construct_policy(pipeline_settings=settings)
    # checking empty policy
    assert policy_json is None

    settings = {'services': {'s3': True}}
    policy_json = construct_policy(app='unicornforrest',
                                   env='stage',
                                   group='forrest',
                                   pipeline_settings=settings)

    # checking s3 policy
    assert type(json.loads(policy_json)) == dict

    # TODO: Test other services besides S3
    settings.update({'services': {'dynamodb': ['coreforrest', 'edgeforrest',
                                               'attendantdevops']}})
    policy_json = construct_policy(pipeline_settings=settings)
    policy = json.loads(policy_json)
