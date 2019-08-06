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
"""Construct a block section of Stages in a Spinnaker Pipeline."""
import logging
from pprint import pformat

from ..utils import get_template

LOG = logging.getLogger(__name__)


def construct_kubernetespipeline(env='',
                                 generated=None,
                                 previous_env=None,
                                 pipeline_data=None):
    """Create the Pipeline JSON from template.

    This handles the common repeatable patterns in a pipeline, such as
    judgement, infrastructure, tagger and qe.

    Args:
        env (str): Deploy environment name, e.g. dev, stage, prod.
        generated (gogoutils.Generator): Gogo Application name generator.
        previous_env (str): The previous deploy environment to use as
            Trigger.
        settings (dict): Environment settings from configurations.

    Returns:
        dict: Pipeline JSON template rendered with configurations.
    """

    # Choose the appropriate kubernetes template based on their decision in pipeline.json file
    k8s_pipeline_type = pipeline_data['kubernetes']['pipeline_type']
    template_name = 'pipeline/pipeline_kubernetes_{}.json.j2'.format(k8s_pipeline_type)
    LOG.debug('using kubernetes.pipeline_type of "%s", template file "%s"', k8s_pipeline_type, template_name)

    gen_app_name = generated.app_name()

    # commenting out until region in kubernetes is figured out
    # ToDo: Figure out region in k8s
    # data = copy.deepcopy(settings)
    data = dict()
    data['app'] = dict()
    data['app'].update({
        'appname': gen_app_name,
        'repo_name': generated.repo,
        'group_name': generated.project,
        'environment': env,
        'region': k8s_pipeline_type,
        'previous_env': previous_env,
        'promote_restrict': pipeline_data['promote_restrict'],
        'owner_email': pipeline_data['owner_email'],
        'manifest_account_name': pipeline_data['kubernetes']['manifest_account_name']
    })

    LOG.debug('Block data:\n%s', pformat(data))

    pipeline_json = get_template(template_file=template_name, data=data, formats=generated)
    return pipeline_json
