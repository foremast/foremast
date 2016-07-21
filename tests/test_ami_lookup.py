"""Ensure AMI names can be translated."""
from foremast.utils import ami_lookup


def test_ami_lookup():
    """Lookup should contact GitLab for JSON table and resolve."""
    assert ami_lookup(name='base_fedora').startswith('ami-xxxx')
    assert ami_lookup(region='us-west-2').startswith('ami-xxxx')
