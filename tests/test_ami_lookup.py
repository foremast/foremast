"""Ensure AMI names can be translated."""
from foremast.utils import ami_lookup


def test_lookup():
    """Lookup should contact GitLab for JSON table and resolve."""
    assert 'ami-xxxx' == ami_lookup(name='base_fedora')
    assert 'ami-xxxx' == ami_lookup(region='us-west-2')
