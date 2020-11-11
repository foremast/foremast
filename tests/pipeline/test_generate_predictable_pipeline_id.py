#   Foremast - Pipeline Tooling
#
#   Copyright 2020 Redbox Automated Retail, LLC
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
"""Test generate_predictable_pipeline_id functionality"""
from foremast.utils.pipelines import generate_predictable_pipeline_id

def test_generate_predictable_pipeline_id():
    """Tests that generate_predictable_pipeline_id creates a matching UUID with identical seed inputs"""
    app_name = "testspinnakerapplication"
    pipeline_name = "testspinnakerpipeline"
    uuid_1 = generate_predictable_pipeline_id(app_name, pipeline_name)
    uuid_2 = generate_predictable_pipeline_id(app_name, pipeline_name)
    assert uuid_1 == uuid_2
