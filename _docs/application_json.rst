================================
application-master-$account.json
================================
Purpose
-------
This configuration file holds infrastruction information for $account. Each AWS account in your pipeline would need a seperate application-master-$account.json file. If your account is named dev, you would want an application-master-dev.json file.

Example Configuration
----------------------
::

    {
        "app": {
            "app_description": null,
            "app_ssh_key": "key_name",
            "email": null,
            "eureka_enabled": false,
            "instance_profile": "instance_profile_name",
            "instance_type": "t2.micro"
        },
        "asg": {
            "hc_type": "ELB",
            "max_inst": 3,
            "min_inst": 1,
            "subnet_purpose": "internal",
            "provider_healthcheck": {
                "amazon": false
            },
            "scaling_policy": {}
        },
        "elb": {
            "certificate": null,
            "health": {
                "interval": 20,
                "threshold": 2,
                "timeout": 10,
                "unhealthy_threshold": 5
            },
            "i_port": 8080,
            "i_proto": "HTTP",
            "lb_port": 80,
            "lb_proto": "HTTP",
            "subnet_purpose": "internal",
            "target": "TCP:8080"
        },
        "qe": {
        },
        "regions": [
            "us-east-1"
        ],
        "deploy_strategy": "highlander",
        "security_group": {
            "description": "Auto-Gen SG for {{ app }}",
            "egress": "0.0.0.0/0",
            "elb_extras": [],
            "ingress": {
                "sg_apps": [
                    {
                        "end_port": "80",
                        "protocol": "tcp",
                        "start_port": "80"
                    },
                    {
                        "end_port": "8080",
                        "protocol": "tcp",
                        "start_port": "8080"
                    }
                ]
            },
            "instance_extras": []
        },
        "dns": {
            "ttl": 60
        }
    }


