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
    """When Eureka is enabled, default Helath Check should be used."""
    eureka_enabled_settings = copy.deepcopy(TEST_SETTINGS)
    eureka_enabled_settings['app']['eureka_enabled'] = True

    health_checks = check_provider_healthcheck(settings=eureka_enabled_settings)
    assert health_checks.providers == ['Discovery']
    assert health_checks.has_healthcheck is True


def test_defined_provider():
    """Provider defined in settings should be returned with capitalization."""
    provider_settings = copy.deepcopy(TEST_SETTINGS)
    provider_settings['asg']['provider_healthcheck']['cloud'] = True
    print(provider_settings)

    health_checks = check_provider_healthcheck(settings=provider_settings)
    assert len(health_checks.providers) == 1
    assert 'cloud' not in health_checks.providers
    assert 'Cloud' in health_checks.providers
    assert health_checks.has_healthcheck is True


def test_additional_provider_with_eureka():
    """Default Provider should be added to providers in settings."""
    eureka_enabled_with_provider_settings = copy.deepcopy(TEST_SETTINGS)
    eureka_enabled_with_provider_settings['app']['eureka_enabled'] = True
    eureka_enabled_with_provider_settings['asg']['provider_healthcheck']['cloud'] = True

    health_checks = check_provider_healthcheck(settings=eureka_enabled_with_provider_settings)
    assert len(health_checks.providers) == 2
    assert 'Discovery' in health_checks.providers
    assert 'cloud' not in health_checks.providers
    assert 'Cloud' in health_checks.providers
    assert health_checks.has_healthcheck is True
