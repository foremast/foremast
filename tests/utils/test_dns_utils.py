"""Test DNS Utils"""

from unittest import mock

import pytest
from foremast.utils.dns import *

MOCK_VALUES = {
    'env': 'dev',
    'zone_id': '/hostedzone/TESTTESTS279',
    'dns_name': 'test.example.com'
}

@mock.patch('foremast.utils.dns.boto3.Session')
def test_find_existing_record(mock_session):
    """Check that a record is found correctly"""
    test_records = [
    {'ResourceRecordSets': [{'Name': 'test.example.com.', 'Type': 'CNAME' }]},
    {'ResourceRecordSets': [{'Name': 'test.example.com.', 'Failover': 'PRIMARY' }]},
    {'ResourceRecordSets': [{'Name': 'test.example.com.', 'Type': 'A' }]}
    ]
    client = mock_session.return_value.client.return_value
    client.get_paginator.return_value.paginate.return_value = test_records
    assert find_existing_record(MOCK_VALUES['env'],
                                MOCK_VALUES['zone_id'],
                                MOCK_VALUES['dns_name'],
                                ['Type', 'CNAME'])
    assert find_existing_record(MOCK_VALUES['env'],
                                MOCK_VALUES['zone_id'],
                                MOCK_VALUES['dns_name'],
                                ['Failover', 'PRIMARY'])
    assert not find_existing_record(MOCK_VALUES['env'],
                                MOCK_VALUES['zone_id'],
                                'bad.example.com',
                                ['Type', 'CNAME'])
