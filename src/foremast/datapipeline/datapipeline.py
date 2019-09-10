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
"""Create Data Pipelines"""

import logging

import boto3
from awscli.customizations.datapipeline import translator

from ..exceptions import DataPipelineDefinitionError
from ..utils import get_details, get_properties

LOG = logging.getLogger(__name__)


class AWSDataPipeline:
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
        self.properties = get_properties(prop_path, env=self.env, region=self.region)
        self.datapipeline_data = self.properties['datapipeline']
        generated = get_details(app=self.app_name)
        self.group = generated.data['project']

        session = boto3.Session(profile_name=self.env, region_name=self.region)
        self.client = session.client('datapipeline')
        self.pipeline_id = None

    def create_datapipeline(self):
        """Creates the data pipeline if it does not already exist

        Returns:
                dict: the response of the Boto3 command
        """

        tags = [{"key": "app_group", "value": self.group}, {"key": "app_name", "value": self.app_name}]
        response = self.client.create_pipeline(
            name=self.datapipeline_data.get('name', self.app_name),
            uniqueId=self.app_name,
            description=self.datapipeline_data['description'],
            tags=tags)
        self.pipeline_id = response.get('pipelineId')

        LOG.debug(response)
        LOG.info("Successfully configured Data Pipeline - %s", self.app_name)
        return response

    def set_pipeline_definition(self):
        """Translates the json definition and puts it on created pipeline

        Returns:
                dict: the response of the Boto3 command
        """

        if not self.pipeline_id:
            self.get_pipeline_id()

        json_def = self.datapipeline_data['json_definition']
        try:
            pipelineobjects = translator.definition_to_api_objects(json_def)
            parameterobjects = translator.definition_to_api_parameters(json_def)
            parametervalues = translator.definition_to_parameter_values(json_def)
        except translator.PipelineDefinitionError as error:
            LOG.warning(error)
            raise DataPipelineDefinitionError

        response = self.client.put_pipeline_definition(
            pipelineId=self.pipeline_id,
            pipelineObjects=pipelineobjects,
            parameterObjects=parameterobjects,
            parameterValues=parametervalues)
        LOG.debug(response)
        LOG.info("Successfully applied pipeline definition")
        return response

    def get_pipeline_id(self):
        """Finds the pipeline ID for configured pipeline"""

        all_pipelines = []
        paginiator = self.client.get_paginator('list_pipelines')
        for page in paginiator.paginate():
            all_pipelines.extend(page['pipelineIdList'])

        for pipeline in all_pipelines:
            if pipeline['name'] == self.datapipeline_data.get('name', self.app_name):
                self.pipeline_id = pipeline['id']
                LOG.info("Pipeline ID Found")
                return
        LOG.info("Pipeline ID Not Found for %s", self.app_name)

    def activate_pipeline(self):
        """Activates a deployed pipeline, useful for OnDemand pipelines"""
        self.client.activate_pipeline(pipelineId=self.pipeline_id)
        LOG.info("Activated Pipeline %s", self.pipeline_id)
