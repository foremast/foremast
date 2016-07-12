================================
application-master-$account.json
================================
Purpose
-------
This configuration file holds infrastruction information for $account. Each AWS account in your pipeline would need a seperate application-master-$account.json file. If your account is named dev, you would want an application-master-dev.json file.

Example Configuration
----------------------

.. literalinclude:: ../src/foremast/templates/configs.json.j2

Configuration Details
----------------------

``app`` : Top level key that contains information on the application and EC2 details

    ``app_description`` : Describes the application.

        | *Default*: Null

    ``app_ssh_key`` : The SSH key that your EC2 instances will use. Must already be created in AWS.

        | *Default*: "{{ account }}_access" (account being the AWS account in the configuration name)

    ``eureka_enabled`` : Setting this value to true will notify the build pipeline to not create an ELB, DNS record, and set the ASG health check to EC2.

        | *Type*: Boolean
        | *Default*: false

    ``instance_profile`` : The instance profile to start EC2 instances with.

        | *Default*: "${stack}_${app}_profile" - Profile with this name will be created by default. Other profiles need to be created before usage

    ``instance_type`` : The size/type of the EC2 instance.

        | *Default*: "t2.micro" - Standard AWS instance names. https://aws.amazon.com/ec2/instance-types/

``asg``: Top level key containing information regarding application ASGs

    ``hc_type`` : ASG Health check type (EC2 or ELB)

        | *Default*: "ELB"
        | *Options*: ("ELB", "EC2")

    ``max_inst`` : Maximum number of instances ASG will scale to.

        | *Type*: int
        | *Default*: 3

    ``min_inst`` : Minimum number of instances your auto-scaling group should have at all times. This is also the default number of instances

        | *Type*: int
        | *Default*: 1

    ``subnet_purpose`` : Determines if the instances should be public (external) or non-public (internal).

        | *Default*: "internal"
        | *Options*: ("internal", "external")

    ``scaling_policy`` : If this block exists, a scaling policy will be attached to the ASG.
        
        ``metrics`` : The metrics to use for auto-scaling. (*Default*: "CPUUtilization", *Options*: ("CPUUtilization", "NetworkIn", "NetworkOut", "DiskReadBytes"))

        ``threshold`` : Metrics number for scaling up (*Type*: int)

        ``period_minutes``: period to look across for determining if threshold was met

        ``statistic``: Stastic to look at the period (*Default*: "Average", *Options*: ("Average", "Maximum", "Minimum", "Sum")

        *Scaling Policy Example*::

          "scaling_policy": {
              "metric": "CPUUtilization",
              "threshold": 90,
              "period_minutes": 10,
              "statistic": "Average"
              }

``elb`` : Top level key for ELB configuration

    ``certificate`` : Name of SSL certification for ELB. SSL certificate must be uploaded to AWS first

        | *Default*: Null

    ``health`` : section for health check details

        ``interval`` : ELB health check interval in seconds. (*Default*: 20)

        ``threshold`` : Number of consecutive health check succeses before declaring EC2 instance healthy. (*Default*: 2)

        ``timeout`` : Health check response timeout in seconds (*Default*: 10)

        ``unhealthy_threshold`` : number of consecutive health check failures before declaring EC2 instance unhealthy (*Default*: 5)

    ``ports`` : Defines ELB listeners. List of listeners with the below keys.

        ``instance`` : The protocol:port of the instance

            | *Default*: "HTTP:8080"

        ``loadbalanacer`` : the protocol:port of the load balancer

            | *Default*: "HTTP:80"

        ``certificate`` : The name of the certificate to use if required

            | *Default*: Null

        *Ports Example*::
 
            "ports": [
                {
                  "instance": "HTTP:8080",
                  "loadbalancer": "HTTP:80"
                },
                {
                  "certificate": "my_cert",
                  "instance": "HTTP:8443",
                  "loadbalancer": "HTTPS:443"
                }
              ]

    ``subnet_purpose`` : Determines if the load balancer should be public (external) or non-public (internal).

        | *Default*: "internal"
        | *Options*: ("internal", "external")

    ``target`` : The check the ELB will use to validate application is online.

        | *Default*: "TCP:8080"

``regions`` : List of AWS regions that application will be deployed to.

        | *Type*: List of strings
        | *Default*: [ "us-east-1" ]

``deploy_strategy`` : Spinnaker strategy to use for deployments.

        | *Default*: "highlander"
        | *Options*: "highlander" (destroy old server group) or "redblack" (disables old server group but do not destroy)

``security_group`` : *to-do*

``dns`` : Top level key for dns settings

    ``ttl`` : sets DNS TTL in seconds

        | *Type*: int
        | *Default*: 60





