"""Test Provider Health Check setting."""
from foremast.pipeline.construct_pipeline_block import check_provider_healthcheck

TEST_SETTINGS = {'app': {'eureka_enabled': False}, 'asg': {'provider_healthcheck': {}}}


def test_provider_healthcheck():
    """Make sure default Provider Health Check works."""
    provider_healthcheck, has_provider_healthcheck = check_provider_healthcheck(settings=TEST_SETTINGS)
    assert provider_healthcheck == []
    assert has_provider_healthcheck == False
