"""Tests for security group duplicates."""
from foremast.utils.security_group  import remove_duplicate_sg

SECURITYGROUP_REPLACEMENTS = {
    'enabled_new_sg': 'old_sg'
}

SECURITY_GROUP_DATA = ['old_sg', 'current_sg', 'enabled_new_sg'] 
VALID_SECURITY_GROUPS = ['current_sg', 'enabled_new_sg']

def test_duplicate_sg_removal():
    """Check that duplicate SGs are removed based on SECURITYGROUP_REPLACEMENTS const."""
    security_groups = remove_duplicate_sg(SECURITY_GROUP_DATA)

    assert security_groups == VALID_SECURITY_GROUPS
