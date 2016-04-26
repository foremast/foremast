import pytest

from pipes.pipeline.utils import check_managed_pipeline


def test_pipeline_names():
    """Only manage names matching **app_name [region]**."""
    app_name = 'unicornforrest'

    with pytest.raises(ValueError):
        check_managed_pipeline(name='something', app_name=app_name)
    with pytest.raises(ValueError):
        check_managed_pipeline(name=app_name, app_name=app_name)

    with pytest.raises(ValueError):
        check_managed_pipeline(name='something [us-east-1', app_name=app_name)
    with pytest.raises(ValueError):
        check_managed_pipeline(name='something us-east-1]', app_name=app_name)
    with pytest.raises(ValueError):
        check_managed_pipeline(name='{0} [us-east-1'.format(app_name),
                               app_name=app_name)
    with pytest.raises(ValueError):
        check_managed_pipeline(name='{0} us-east-1]'.format(app_name),
                               app_name=app_name)

    with pytest.raises(ValueError):
        check_managed_pipeline(name='some some', app_name=app_name)
    with pytest.raises(ValueError):
        check_managed_pipeline(name='some some [us-east-1]', app_name=app_name)

    with pytest.raises(ValueError):
        check_managed_pipeline(name='something [us-east-1]', app_name=app_name)

    assert 'us-east-1' == check_managed_pipeline(
        name='{0} [us-east-1]'.format(app_name),
        app_name=app_name)
