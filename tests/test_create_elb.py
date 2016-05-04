"""Test ELB creation functions."""
from foremast.elb.format_listeners import format_listeners
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


def test_format_listeners():
    """Listeners should be formatted in list of dicts."""
    test = {
        'certificate': None,
        'i_port': 8080,
        'i_proto': 'HTTP',
        'lb_port': 80,
        'lb_proto': 'HTTP'
    }
    sample = [{
        'externalPort': 80,
        'externalProtocol': 'HTTP',
        'internalPort': 8080,
        'internalProtocol': 'HTTP',
        'sslCertificateId': None
    }]

    results = format_listeners(elb_settings=test)
    for index, result in enumerate(results):
        assert sorted(sample[index]) == sorted(result)
    assert sample == results

    test = {'ports': [{'instance': 'HTTP:8080', 'loadbalancer': 'http:80'}]}

    assert sample == format_listeners(elb_settings=test)

    test['ports'].append({
        'certificate': 'kerby',
        'instance': 'http:80',
        'loadbalancer': 'https:443',
    })
    sample.append({
        'externalPort': 443,
        'externalProtocol': 'HTTPS',
        'internalPort': 80,
        'internalProtocol': 'HTTP',
        'sslCertificateId': 'kerby',
    })

    assert sample == format_listeners(elb_settings=test)
