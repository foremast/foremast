#   Foremast - Pipeline Tooling
#
#   Copyright 2016 Gogo, LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

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

    assert sample == format_listeners(elb_settings=test)

    # 'ports' key should override old style definitions
    test['ports'] = [{'instance': 'HTTP:8000', 'loadbalancer': 'http:500'}]
    sample = [{
        'externalPort': 500,
        'externalProtocol': 'HTTP',
        'internalPort': 8000,
        'internalProtocol': 'HTTP',
        'sslCertificateId': None
    }]

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
