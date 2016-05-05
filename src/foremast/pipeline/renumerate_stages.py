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
    for stage in stages:
        if stage['name'].startswith('Git Tag'):
            stage['requisiteStageRefIds'] = [str(main_index)]
            stage['refId'] = str(main_index * 100)
        elif stage['type'] == 'bake':
            stage['requisiteStageRefIds'] = []
            stage['refId'] = str(main_index)
        else:
            stage['requisiteStageRefIds'] = [str(main_index)]
            main_index += 1
            stage['refId'] = str(main_index)

        LOG.debug('step=%(name)s\trefId=%(refId)s\t'
                  'requisiteStageRefIds=%(requisiteStageRefIds)s', stage)

    return pipeline
