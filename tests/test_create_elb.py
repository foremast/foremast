"""Test ELB creation functions."""
from foremast.elb.splay_health import splay_health


def test_splay():
    """Splay should split Health Checks properly."""
    health = splay_health('HTTP:80/test')
    assert health.path == '/test'
    assert health.port == '80'
    assert health.proto == 'HTTP'
    assert health.target == 'HTTP:80/test'

    health = splay_health('TCP:8000/test')
    assert health.path == ''
    assert health.port == '8000'
    assert health.proto == 'TCP'
    assert health.target == 'TCP:8000'

    health = splay_health('HTTPS:8000/test')
    assert health.path == '/test'
    assert health.port == '8000'
    assert health.proto == 'HTTPS'
    assert health.target == 'HTTPS:8000/test'

    health = splay_health('HTTPS:80')
    assert health.path == '/healthcheck'
    assert health.port == '80'
    assert health.proto == 'HTTPS'
    assert health.target == 'HTTPS:80/healthcheck'
