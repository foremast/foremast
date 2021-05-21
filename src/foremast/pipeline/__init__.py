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
"""Package for the creation of spinnaker pipelines"""
from .create_pipeline import SpinnakerPipeline
from .create_pipeline_datapipeline import SpinnakerPipelineDataPipeline
from .create_pipeline_stepfunction import SpinnakerPipelineStepFunction
from .create_pipeline_lambda import SpinnakerPipelineLambda
from .create_pipeline_manual import SpinnakerPipelineManual
from .create_pipeline_onetime import SpinnakerPipelineOnetime
from .create_pipeline_s3 import SpinnakerPipelineS3
from .create_pipeline_cloudfunction import SpinnakerPipelineCloudFunction
