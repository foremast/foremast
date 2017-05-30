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

import awscli.customizations.datapipeline.translator as translator
import boto3
from tryagain import retries

from ..utils import get_details, get_properties

LOG = logging.getLogger(__name__)


class AWSDataPipeline(object):
    """Manipulate Data Pipeline."""

    def __init__(self, app=None, env=None, region='us-east-1', prop_path=None):
        """AWS Data Pipeline object.

        Args:
            app (str): Application name
            env (str): Environment/Account
            region (str): AWS Region
            prop_path (str): Path of environment property file
        """
        self.app_name = app
        self.env = env
        self.region = region
        self.properties = get_properties(prop_path)
        self.datapipeline_data = self.properties[self.env]['datapipeline']
        generated = get_details(app=self.app_name)
        self.group = generated.data['project']

        session = boto3.Session(profile_name=self.env, region_name=self.region)
        self.client = session.client('datapipeline')
        self.pipeline_id = None

    def create_datapipeline(self):
        """Creates the data pipeline if it does not already exist"""

        tags = [
                {"key": "app_group",
                "value": self.group},
                {"key": "app_name",
                "value": self.app_name}
                ]
        response = self.client.create_pipeline(name=self.datapipeline_data.get('name', self.app_name),
                                               uniqueId=self.app_name,
                                               description=self.datapipeline_data['description'],
                                               tags=tags)
        self.pipeline_id = response.get('pipelineId')
        LOG.debug(response)
        LOG.info("Successfully configured Data Pipeline - %s", self.app_name)

    def set_pipeline_definition(self):
        """Translates the json definition and puts it on created pipeline"""

        if not self.pipeline_id:
            self.get_pipeline_id()

        pipelineObjects = translator.definition_to_api_objects(self.datapipeline_data['json_definition'])
        parameterObjects = translator.definition_to_api_parameters(self.datapipeline_data['json_definition'])
        parameterValues = translator.definition_to_parameter_values(self.datapipeline_data['json_definition'])
        response = self.client.put_pipeline_definition(
                                pipelineId=self.pipeline_id,
                                pipelineObjects=pipelineObjects,
                                parameterObjects=parameterObjects,
                                parameterValues=parameterValues)
        LOG.debug(response)
        LOG.info("Successfully applied pipeline definition")

    def get_pipeline_id(self):
        """Finds the pipeline ID for configured pipeline"""

        all_pipelines = []
        hasMore = True
        marker = None
        # handles the pagination from boto3
        while hasMore:
            if not marker:
                response = self.client.list_pipelines()
            else:
                LOG.info("Checking for more pipelines")
                response = self.client.list_pipelines(marker=marker)
            all_pipelines.extend(response['pipelineIdList'])
            hasMore = response['hasMoreResults']
            marker = response.get('marker')
            LOG.debug(response)
        
        for pipeline in all_pipelines:
            if pipeline['name'] == self.datapipeline_data.get('name', self.app_name):
                self.pipeline_id = pipeline['id']
                LOG.info("Pipeline ID Found")
                return
        LOG.info("Pipeline ID Not Found for %s", self.app_name)
