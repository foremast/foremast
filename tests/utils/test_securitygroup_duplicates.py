"""Tests for security group duplicates."""
from unittest import mock

from foremast.utils.security_group  import remove_duplicate_sg

SECURITYGROUP_REPLACEMENTS = {
    'enabled_new_sg': 'old_sg'
}

SECURITY_GROUP_DATA = ['old_sg', 'current_sg', 'enabled_new_sg'] 
VALID_SECURITY_GROUPS = ['current_sg', 'enabled_new_sg']


def test_duplicate_sg_removal():
    """Check that duplicate SGs are removed based on SECURITYGROUP_REPLACEMENTS const."""
    with mock.patch.dict('foremast.utils.security_group.SECURITYGROUP_REPLACEMENTS', SECURITYGROUP_REPLACEMENTS):
        security_groups = remove_duplicate_sg(SECURITY_GROUP_DATA)
        assert security_groups == VALID_SECURITY_GROUPS
