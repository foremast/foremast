"""Test default Security Groups."""
from unittest import mock

from foremast.securitygroup.create_securitygroup import SpinnakerSecurityGroup


@mock.patch('foremast.securitygroup.create_securitygroup.get_details')
@mock.patch('foremast.securitygroup.create_securitygroup.get_properties')
def test_default_security_groups(mock_properties, mock_details):
    """Make sure default Security Groups are added to the ingress rules."""
    ingress = {
        'test_app': [
            {
                'start_port': 30,
                'end_port': 30,
            },
        ],
    }

    mock_properties.return_value = {
        'security_group': {
            'ingress': ingress,
            'description': '',
        },
    }

    test_sg = {
        'myapp': [
            {
                'start_port': '22',
                'end_port': '22',
                'protocol': 'tcp'
            },
        ]
    }
    with mock.patch.dict('foremast.securitygroup.create_securitygroup.DEFAULT_SECURITYGROUP_RULES', test_sg):
        sg = SpinnakerSecurityGroup()
        ingress = sg.update_default_rules()
        assert 'myapp' in ingress
