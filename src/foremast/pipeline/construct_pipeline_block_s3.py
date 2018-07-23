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
import copy
import logging
from pprint import pformat

from ..utils import get_template

LOG = logging.getLogger(__name__)


def construct_pipeline_block_s3(env='',
                                generated=None,
                                previous_env=None,
                                region='us-east-1',
                                settings=None,
                                pipeline_data=None):
    """Create the Pipeline JSON from template.

    This handles the common repeatable patterns in a pipeline, such as
    judgement, infrastructure, tagger and qe.

    Args:
        env (str): Deploy environment name, e.g. dev, stage, prod.
        generated (gogoutils.Generator): Gogo Application name generator.
        previous_env (str): The previous deploy environment to use as
            Trigger.
        region (str): AWS Region to deploy to.
        settings (dict): Environment settings from configurations.

    Returns:
        dict: Pipeline JSON template rendered with configurations.
    """
    LOG.info('%s block for [%s].', env, region)

    if env.startswith('prod'):
        template_name = 'pipeline/pipeline_{}_s3.json.j2'.format(env)
    else:
        template_name = 'pipeline/pipeline_stages_s3.json.j2'

    LOG.debug('%s info:\n%s', env, pformat(settings))

    gen_app_name = generated.app_name()

    data = copy.deepcopy(settings)

    data['app'].update({
        'appname': gen_app_name,
        'repo_name': generated.repo,
        'group_name': generated.project,
        'environment': env,
        'region': region,
        'previous_env': previous_env,
        'promote_restrict': pipeline_data['promote_restrict'],
        'owner_email': pipeline_data['owner_email']
    })

    LOG.debug('Block data:\n%s', pformat(data))

    pipeline_json = get_template(template_file=template_name, data=data, formats=generated)
    return pipeline_json
