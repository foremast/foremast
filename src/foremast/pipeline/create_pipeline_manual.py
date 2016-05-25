"""Create Pipelines for Spinnaker."""
import collections
import json
import logging
import os
from pprint import pformat

import requests

from ..consts import API_URL
from ..exceptions import SpinnakerPipelineCreationFailed
from ..utils import (ami_lookup, get_app_details, get_subnets,
                     get_template, get_properties)
from .clean_pipelines import clean_pipelines
from .construct_pipeline_block import construct_pipeline_block
from .renumerate_stages import renumerate_stages
from .create_pipeline import SpinnakerPipeline

class SpinnakerPipelineManual(SpinnakerPipeline):
    """Manipulate Spinnaker Pipelines.

    Args:
        app_name: Str of application name.
    """

    def __init__(self, app_info):
        super().__init__(app_info)
        self.environments = [self.app_info['env']]

    def post_pipeline(self, pipeline):
        """Send Pipeline JSON to Spinnaker."""

        if isinstance(pipeline, str):
            pipeline_str = pipeline
        else:
            pipeline_str = json.dumps(pipeline)

        pipeline_json = json.loads(pipeline_str)

        # Note pipeline name is manual
        name = '{0} (onetime-{1})'.format(pipeline_json['name'], self.environments[0])
        pipeline_json['name'] = name

        # disable trigger as not to accidently kick off multiple deployments
        for trigger in pipeline_json['triggers']:
            trigger['enabled'] = False

        self.log.debug('Manual Pipeline JSON:\n%s', pipeline_json)
        super().post_pipeline(pipeline_json)
