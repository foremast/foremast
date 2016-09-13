"""Test Provider Health Check setting."""
import copy

from foremast.pipeline.construct_pipeline_block import check_provider_healthcheck

TEST_SETTINGS = {'app': {'eureka_enabled': False}, 'asg': {'provider_healthcheck': {}}}


def test_provider_healthcheck():
    """Make sure default Provider Health Check works."""
    health_checks = check_provider_healthcheck(settings=TEST_SETTINGS)
    assert health_checks.providers == []
    assert health_checks.has_healthcheck == False


def test_setting_eureka_enabled():
    """When Eureka is enabled, Amazon EC2 Helath Check should be used."""
    eureka_enabled_settings = copy.copy(TEST_SETTINGS)
    eureka_enabled_settings['app']['eureka_enabled'] = True

    health_checks = check_provider_healthcheck(settings=eureka_enabled_settings)
    assert health_checks.providers == ['Amazon']
    assert health_checks.has_healthcheck is True
