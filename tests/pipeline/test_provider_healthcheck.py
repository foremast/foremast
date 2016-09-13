"""Test Provider Health Check setting."""
from foremast.pipeline.construct_pipeline_block import check_provider_healthcheck

TEST_SETTINGS = {'app': {'eureka_enabled': False}, 'asg': {'provider_healthcheck': {}}}


def test_provider_healthcheck():
    """Make sure default Provider Health Check works."""
    health_checks = check_provider_healthcheck(settings=TEST_SETTINGS)
    assert health_checks.providers == []
    assert health_checks.has_healthcheck == False
