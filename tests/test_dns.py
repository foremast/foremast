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


@patch('foremast.dns.create_dns.boto3.session.Session')
@patch('foremast.dns.create_dns.get_properties')
@patch('foremast.dns.create_dns.get_details')
def test_dns_creation(dns_mock, properties_mock, aws_session_mock):
    d = dns.SpinnakerDns(region='region1', env='dev1', elb_subnet='noexist')
    dns_mock.app_name = MagicMock(return_value='myapp')
    assert d.domain == 'example.com'
    assert d.region == 'region1'
    assert d.elb_subnet == 'noexist'
