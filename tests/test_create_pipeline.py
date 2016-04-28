import pytest

from foremast.utils import check_managed_pipeline


def test_pipeline_names():
    """Only manage names matching **app_name [region]**."""
    app_name = 'unicornforrest'

    bad_names = [
        'something',
        app_name,
        'something [us-east-1',
        'something us-east-1]',
        '{0} [us-east-1'.format(app_name),
        '{0} us-east-1]'.format(app_name),
        'some some',
        'something [us-east-1]',
        'some some [us-east-1]',
        ]

    for name in bad_names:
        with pytest.raises(ValueError):
            check_managed_pipeline(name=name, app_name=app_name)

    assert 'us-east-1' == check_managed_pipeline(
        name='{0} [us-east-1]'.format(app_name),
        app_name=app_name)
