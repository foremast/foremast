"""Verifies that instance_links are being retrieved properly from LINKS. Verifies that app_data.json.j2
contains the instance link information"""
from unittest import mock
from foremast import configs

TEST_CONFIG =  { 
    "asg": {
        "subnet_purpose": "internal",
        "min_inst": 3,
        "max_inst": 3
    },
    "regions": {
        "us-east-1": {},
        "us-west-2": {
            "asg": {
                "min_inst": 1,
                "max_inst": 1
            }
        }
    }
}

def test_appy_region_configs():
    """Tests that `configs.apply_region_configs` applies
    region specific overrides correctly""" 
    desired_config = { 
        "asg": {
            "subnet_purpose": "internal",
            "min_inst": 3,
            "max_inst": 3
        },
        "regions": {
            "us-east-1": {},
            "us-west-2": {
                "asg": {
                    "min_inst": 1,
                    "max_inst": 1
                }
            }
        },
        "us-east-1": { 
            "asg": {
                "subnet_purpose": "internal",
                "min_inst": 3,
                "max_inst": 3
            },
            "regions": {
                "us-east-1": {},
                "us-west-2": {
                    "asg": {
                        "min_inst": 1,
                        "max_inst": 1
                    }
                }
            }
        },
        "us-west-2": { 
            "asg": {
                "subnet_purpose": "internal",
                "min_inst": 1,
                "max_inst": 1
            },
            "regions": {
                "us-east-1": {},
                "us-west-2": {
                    "asg": {
                        "min_inst": 1,
                        "max_inst": 1
                    }
                }
            }
        }
    }
    rendered_config = configs.apply_region_configs(TEST_CONFIG)
    assert rendered_config == desired_config

def test_legacy_region_format():
    """Validates that the only regions list format continues to work."""
    desired_config = {
        "asg": {
            "subnet_purpose": "internal",
            "min_inst": 3,
            "max_inst": 3
        },
        "regions": ["us-east-1", "us-west-2"],
        "us-east-1": {
            "asg": {
                "subnet_purpose": "internal",
                "min_inst": 3,
                "max_inst": 3
            },
            "regions": ["us-east-1", "us-west-2"],
        },
        "us-west-2": {
            "asg": {
                "subnet_purpose": "internal",
                "min_inst": 3,
                "max_inst": 3
            },
            "regions": ["us-east-1", "us-west-2"],
        },
    }
    legacy_config = TEST_CONFIG.copy()
    legacy_config["regions"] = ['us-east-1', 'us-west-2']
    rendered_config = configs.apply_region_configs(legacy_config)
    assert rendered_config == desired_config



    
