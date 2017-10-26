"""Test Subnet data."""
from unittest import mock

import pytest

from foremast.exceptions import SpinnakerSubnetError, SpinnakerTimeout
from foremast.utils.subnets import get_subnets

SUBNET_DATA = [
    {
        'vpcId': 100,
        'account': 'dev',
        'id': 1,
        'purpose': 'internal',
        'region': 'us-east-1',
        'target': 'ec2',
        'availabilityZone': []
    },
    {
        'vpcId': 101,
        'account': 'dev',
        'id': 2,
        'purpose': 'other',
        'region': 'us-west-2',
        'target': 'ec2',
        'availabilityZone': ['us-west-2a', 'us-west-2b']
    },
]


@mock.patch('foremast.utils.subnets.requests.get')
def test_utils_subnets_get_subnets(mock_requests_get):
    """Find one subnet."""
    mock_requests_get.return_value.json.return_value = SUBNET_DATA

    # default - happy path
    result = get_subnets(env='dev', region='us-east-1')
    assert result == {
        'subnet_ids': {
            'us-east-1': [SUBNET_DATA[0]['id']],
        },
        'us-east-1': [[]],
    }


@mock.patch('foremast.utils.subnets.requests.get')
def test_utils_subnets_get_subnets_multiple_az(mock_requests_get):
    """Find multiple Availability Zones."""
    mock_requests_get.return_value.json.return_value = SUBNET_DATA

    # default - happy path w/multiple az
    result = get_subnets(env='dev', region='')
    assert result == {'dev': {'us-west-2': [['us-west-2a', 'us-west-2b']], 'us-east-1': [[]]}}


@mock.patch('foremast.utils.subnets.requests.get')
def test_utils_subnets_get_subnets_subnet_not_found(mock_requests_get):
    """Trigger SpinnakerSubnetError when no subnets found."""
    mock_requests_get.return_value.json.return_value = SUBNET_DATA

    # subnet not found
    with pytest.raises(SpinnakerSubnetError):
        result = get_subnets(env='dev', region='us-west-1')
        assert result == {'us-west-1': [[]]}


@mock.patch('foremast.utils.subnets.requests.get')
def test_utils_subnets_get_subnets_api_error(mock_requests_get):
    """Trigger SpinnakerTimeout when API has error."""
    mock_requests_get.return_value.json.return_value = SUBNET_DATA

    # error getting details
    with pytest.raises(SpinnakerTimeout):
        mock_requests_get.return_value.ok = False
        result = get_subnets()
