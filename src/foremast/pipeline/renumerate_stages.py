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

    +---------+------------------------+------------+
    | refId   | stage                  | requires   |
    +=========+========================+============+
    | 0       | config                 |            |
    +---------+------------------------+------------+
    | 1       | bake                   |            |
    +---------+------------------------+------------+
    | 100     | git tagger packaging   | 1          |
    +---------+------------------------+------------+
    | 2       | deploy dev             | 1          |
    +---------+------------------------+------------+
    | 3       | QE dev                 | 2          |
    +---------+------------------------+------------+
    | 202     | Attach Scaling Policy  | 2          |
    +---------+------------------------+------------+
    | 200     | git tagger dev         | 2          |
    +---------+------------------------+------------+
    | 4       | judgement              | 3          |
    +---------+------------------------+------------+
    | 5       | deploy stage           | 4          |
    +---------+------------------------+------------+
    | 6       | QE stage               | 5          |
    +---------+------------------------+------------+
    | 500     | git tagger stage       | 5          |
    +---------+------------------------+------------+

    Args:
        pipeline (dict): Completed Pipeline ready for renumeration.

    Returns:
        dict: Pipeline ready to be sent to Spinnaker.
    """
    stages = pipeline['stages']

    main_index = 1
    for idx, stage in enumerate(stages):
        if stage['name'].startswith('Git Tag'):
            stage['requisiteStageRefIds'] = [str(main_index)]
            stage['refId'] = str(main_index * 100)
        elif stage['name'].startswith('Attach Scaling'):
            stage['requisiteStageRefIds'] = [str(main_index)]
            stage['refId'] = str(main_index * 101)
        elif stage['name'].startswith('ServiceNow'):
            stage['requisiteStageRefIds'] = [str(main_index)]
            stage['refId'] = str(main_index * 102)
        elif stage['type'] == 'bake' or idx == 0:
            stage['requisiteStageRefIds'] = []
            stage['refId'] = str(main_index)
        else:
            stage['requisiteStageRefIds'] = [str(main_index)]
            main_index += 1
            stage['refId'] = str(main_index)

        LOG.debug('step=%(name)s\trefId=%(refId)s\t'
                  'requisiteStageRefIds=%(requisiteStageRefIds)s', stage)

    return pipeline
