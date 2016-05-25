"""Create Pipelines for Spinnaker."""
import json

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
