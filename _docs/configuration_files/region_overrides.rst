.. _region_overrides:

=========================
Region Specific Overrides
=========================

.. contents::
   :local:

Purpose
-------

Within the `application.json` configuration, the need may arise to us different settings for different regions.
You can override any setting in the `regions` blocks and that will be applied to only a specific region. 

Example
-------

.. code-block:: json

   {
        "security_group": {
            "description": "something useful",
            "elb_extras": [],
            "instance_extras": ["offices_all"]
        },
        "app": {
            "instance_type": "t2.small",
            "app_description": "Edge Forrest Demo application",
            "instance_profile": "forrest_edge_profile"
        },
        "elb": {
            "subnet_purpose": "internal",
            "target": "TCP:8080",
            "ports": [
            {"loadbalancer": "HTTP:80", "instance": "HTTP:8080"}
            ]
        },
        "asg": {
            "subnet_purpose": "internal",
            "min_inst": 1,
            "max_inst": 1
        },
        "dns" : { "ttl": 120 },
        "regions": {
            "us-east-1": {}
            "us-west-2": {
                "app": {
                    "instance_type": "t2.medium"
                }
                "asg": {
                    "min_inst": 5
                    "max_inst": 10
                }
            }
        }
    }

In the above example, under the `regions` blocks region-specific configs are set for
`us-west-2`. These configs override what is in the main json block. `us-east-1` just
has an empty `{}` and so no settings are specifically overriden and it will just use
values from the main json block. 