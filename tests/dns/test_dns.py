#   Foremast - Pipeline Tooling
#
#   Copyright 2018 Gogo, LLC
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

from unittest.mock import MagicMock, patch

from foremast import dns


@patch('foremast.dns.create_dns.update_dns_zone_record')
@patch('foremast.dns.create_dns.get_dns_zone_ids')
@patch('foremast.dns.create_dns.find_elb')
@patch('foremast.dns.create_dns.get_properties')
@patch('foremast.dns.create_dns.DOMAIN', 'example.com')
@patch('foremast.dns.create_dns.get_details')
def test_dns_creation(mock_get_details, mock_properties, mock_find_elb, mock_dns_zones, mock_update_dns):
    # mocked data
    hosted_zones = [500, 501]
    dns_elb = {'elb': 'myapp.dev1.example.com'}

    # mock results
    mock_get_details.return_value.app_name.return_value = 'myapp'
    mock_get_details.return_value.dns.return_value = dns_elb
    mock_properties.return_value = {'dns': {'ttl': 60}}
    mock_find_elb.return_value = 'myapp-internal.domain.external.com'
    mock_dns_zones.return_value = hosted_zones
    mock_update_dns.return_value = True

    d = dns.SpinnakerDns(app='myapp', region='region1', env='dev1', elb_subnet='noexist')
    assert d.domain == 'example.com'
    assert d.region == 'region1'
    assert d.elb_subnet == 'noexist'
    assert d.app_name == 'myapp'

    assert 'myapp.dev1.example.com' == d.create_elb_dns()

    sent_update_data = {
        'dns_name': dns_elb['elb'],
        'dns_name_aws': mock_find_elb.return_value,
        'dns_ttl': mock_properties.return_value['dns']['ttl']
    }

    mock_update_dns.assert_called_with('dev1', 501, **sent_update_data)
    assert mock_update_dns.call_count == 2
