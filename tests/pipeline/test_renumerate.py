from foremast.pipeline.renumerate_stages import renumerate_stages


def test_basic():
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
                'requisiteStageRefIds': ['1'],
            },
            {
                'refId': '201',
                'requisiteStageRefIds': ['1'],
            },
            {
                'refId': '202',
                'requisiteStageRefIds': ['1'],
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
