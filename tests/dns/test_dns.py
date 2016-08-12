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

from foremast import dns
from unittest.mock import patch, MagicMock


@patch('foremast.dns.create_dns.json.loads')
@patch('foremast.dns.create_dns.find_elb')
@patch('foremast.dns.create_dns.boto3.session.Session')
@patch('foremast.dns.create_dns.get_properties')
@patch('foremast.dns.create_dns.get_details')
def test_dns_creation(mock_get_details, mock_properties, mock_aws_session, mock_find_elb, mock_json):
    # mocked data
    hosted_zones = {
        'HostedZones': [
            {'Config': {'PrivateZone': True}, 'Id': 500},
            {'Config': {'PrivateZone': False}, 'Id': 501},
        ]
    }

    dns_elb = {
        'elb': 'myapp.dev1.example.com'
    }

    # mock results
    mock_get_details.return_value.app_name.return_value = 'myapp'
    mock_get_details.return_value.dns.return_value = dns_elb
    mock_find_elb.return_value = 'myapp-internal.domain.external.com'
    mock_aws_session.return_value.client.return_value.list_hosted_zones_by_name.return_value = hosted_zones
    mock_aws_session.return_value.client.return_value.change_resource_record_sets.return_value = True

    d = dns.SpinnakerDns(app='myapp', region='region1', env='dev1', elb_subnet='noexist')
    assert d.domain == 'example.com'
    assert d.region == 'region1'
    assert d.elb_subnet == 'noexist'
    assert d.app_name == 'myapp'

    assert 'myapp.dev1.example.com' == d.create_elb_dns()
