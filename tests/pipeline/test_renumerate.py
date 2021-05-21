"""Test Stage renumerate logic."""
from foremast.pipeline.renumerate_stages import renumerate_stages


def test_basic():
    """Should be sequential Stage IDs.
    Examples:
        Graphically:

        .. code-block:: text

            [ 1 ]-[ 2 ]-[ 3 ]
    """
    pipeline = {
        'stages': [
            {
                'refId': 'master',
            },
            {
                'refId': 'master',
            },
            {
                'refId': 'master',
            },
        ],
    }

    answer = {
        'stages': [
            {
                'refId': '1',
                'requisiteStageRefIds': [],
            },
            {
                'refId': '2',
                'requisiteStageRefIds': ['1'],
            },
            {
                'refId': '3',
                'requisiteStageRefIds': ['2'],
            },
        ],
    }

    assert renumerate_stages(pipeline) == answer


def test_branches():
    """Test 'branch' Stages refer to correct 'master' level.

    Examples:
        Graphically:

        .. code-block:: text

            [ 1 ]-[ 2 ]-[ 3 ]-[ 4 ]
                    L---[200]
                    L---[201]
                    L---[202]
    """
    pipeline = {
        'stages': [
            {
                'refId': 'master',
            },
            {
                'refId': 'master',
            },
            {
                'refId': 'branch',
            },
            {
                'refId': 'branch',
            },
            {
                'refId': 'branch',
            },
            {
                'refId': 'master',
            },
            {
                'refId': 'master',
            },
        ],
    }

    answer = {
        'stages': [
            {
                'refId': '1',
                'requisiteStageRefIds': [],
            },
            {
                'refId': '2',
                'requisiteStageRefIds': ['1'],
            },
            {
                'refId': '200',
                'requisiteStageRefIds': ['2'],
            },
            {
                'refId': '201',
                'requisiteStageRefIds': ['2'],
            },
            {
                'refId': '202',
                'requisiteStageRefIds': ['2'],
            },
            {
                'refId': '3',
                'requisiteStageRefIds': ['2'],
            },
            {
                'refId': '4',
                'requisiteStageRefIds': ['3'],
            },
        ],
    }

    assert renumerate_stages(pipeline) == answer
