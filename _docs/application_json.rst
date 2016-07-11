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

Configuration Detail
--------------------

:code:`app` : This top level key contains information on the application and EC2 details

    :code:`app_description` : Describe your application. Not directly used in pipelines

    :code:`app_ssh_key` : The SSH key that your EC2 instances will use. Must alreaady be created in AWS.
    *default*: "{{ account }}_access"

    :code:`eureka_enabled` : Setting this value to true will notify the build pipeline to not create an ELB, DNS record, and set the ASG health check to EC2.
    *default*: false

    :code:`instance_profile` : The instance profile to start instances with.
    *default*: "${stack}_${app}_profile"

    :code:`instance_type` : The size of the EC2 instance.
    *default*: "t2.micro"


:code:`asg`: Top level key containing information regarding the ASGs

    :code:`hc_type` : Health check type (EC2 or ELB)
    *default*: "ELB"

    :code:`max_inst` : Maximum number of instances you will scale to. This only occurs once load is high enough to require additional instances above min_inst setting.

    :code:`min_inst` : Minimum number of instances your auto-scaling group should have at all times

    :code:`subnet_purpose` : Determines if the instances should be public (external) or non-public (internal), you likely want internal.

    :code:`scaling_policy` : *to do*

:code:`elb` : Top loevel key for ELB configuration

    :code:`certificate` : Name of SSL certification for ELB
    
    :code:`health` : section for health check details

        :code:`interval` : ELB health check interval in seconds

        :code:`threshold` : Number of consecutive health check succeses before declaring EC2 instance healthy

        :code:`timeout` : Health check response timeout, seconds

        :code:`unhealthy_threshold` : number of consecutive health check failures before declaring EC2 instance unhealthy

    :code:`ports` : *to do*

    :code:`subnet_purpose` : Determines if the load balancer should be public (external) or non-public (internal), you likely want internal

    :code:`target` : The check ELB will use to validate your application is online.




