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

"""Renumerate the Pipeline Stages."""
import logging

LOG = logging.getLogger(__name__)


def renumerate_stages(pipeline):
    """Renumber Pipeline Stage reference IDs to account for dependencies.
       stage order is defined in the templates.
       refId == 'a' - Any mainline required stage
       refId == 'b' - Any secondary stage that should be ran in parallel

    Args:
        pipeline (dict): Completed Pipeline ready for renumeration.

    Returns:
        dict: Pipeline ready to be sent to Spinnaker.
    """
    stages = pipeline['stages']

    main_index = 0
    for stage in stages:
        if stage['refId'] == 'a':
            if main_index == 0:
                stage['requisiteStageRefIds'] = []
            else:
                stage['requisiteStageRefIds'] = [str(main_index)]
            main_index += 1
            stage['refId'] = str(main_index)
        elif stage['refId'] == 'b':
            stage['refId'] = str(main_index*100)
            stage['requisiteStageRefIds'] = [str(main_index)]

        LOG.debug('step=%(name)s\trefId=%(refId)s\t'
                  'requisiteStageRefIds=%(requisiteStageRefIds)s', stage)

    return pipeline
