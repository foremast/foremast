.. _application_json:

================================
application-master-$account.json
================================

.. contents::
   :local:

Purpose
-------
This configuration file holds infrastruction information for $account. Each AWS account in your pipeline would need a seperate application-master-$account.json file. If your account is named dev, you would want an application-master-dev.json file.

Example Configuration
----------------------

.. literalinclude:: ../../src/foremast/templates/configs/configs.json.j2

Configuration Details
----------------------

``app`` Block
~~~~~~~~~~~~~

Top level key that contains information on the application and EC2 details

``app_description``
************************

Describes the application.

    | *Default*: ``null``

``eureka_enabled``
***********************

Setting this value to ``true`` will not create an ELB, DNS record, and set the ASG health check to EC2.

    | *Type*: Boolean
    | *Default*: ``false``

``instance_profile``
**************************

The instance profile to start EC2 instances with.

    | *Default*: ``"${stack}_${app}_profile"`` - Profile with this name will be created by default. Other profiles need to be created before usage

``instance_type``
**********************

The size/type of the EC2 instance. Uses Standard AWS instance names. See https://aws.amazon.com/ec2/instance-types/ for details

    | *Default*: ``"t2.micro"``

``lambda_environment``
**********************

Environment variables which are passed to the lambda function.

``lambda_environment`` *Keys*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    ``Variables`` : Dictionary of environment variables.

        | *Type*: Dict
        | *Default*: ``null``

``lambda_environment`` *Example*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

      "environment": {
          "Variables": {
              "VAR1": "val1",
              "VAR2": "val2",
              "VAR3": "val3"
          }
      }

``lambda_memory``
*****************

The amount of memory to give a Lambda function

    | *Default*: ``"128"``
    | *Units*: Megabytes

``lambda_role``
***************

Override the default generated IAM Role name.

    | *Default*: ``"${stack}_${app}_role"``

``lambda_timeout``
******************

The timeout setting for Lambda function

    | *Default*: ``"3600"``
    | *Units*: Seconds

``asg`` Block
~~~~~~~~~~~~~

Top level key containing information regarding application ASGs

``hc_type``
************

ASG Health check type (EC2 or ELB)

    | *Default*: ``"ELB"``
    | *Options*:

       - ``"ELB"``
       - ``"EC2"``

``app_grace_period``
********************

App specific health check grace period (added onto default ASG healthcheck grace period) to delay sending
of health check requests. This is useful in the event your application takes longer to boot than the
default hc_grace_period defined in templates. For example, hc_grace_period may be 180 seconds, but an app
may need a variable amount of time to boot (say 30 seconds extra). This will add 180 + 30 to calculate
the overall hc_grace_period of 210 seconds.

    | *Default*: ``0``
    | *Units*: Seconds

``max_inst``
*************

Maximum number of instances ASG will scale to.

    | *Type*: int
    | *Default*: ``3``

``min_inst``
************

Minimum number of instances your auto-scaling group should have at all times. This is also the default number of instances

    | *Type*: int
    | *Default*: ``1``

``ssh_keypair``
*******************

SSH key that your EC2 instances will use. Must already be created in AWS. This replaces the non-functional and deprecated app_ssh_key configuration key.

    | *Default*: ``"{{ account }}_{{ region }}_default"`` - {{ account }} being the AWS account in the configuration name

``subnet_purpose``
******************

Determines if the instances should be public (external) or non-public (internal).

    | *Default*: ``"internal"``
    | *Options*

       - ``"internal"``
       -  ``"external"``

``enable_public_ips``
*********************

Determines if instances in an cluster should have public IPs associated. By default, this is set to null which means it uses default behavior configured for your subnets in your cloud provider.

    | *Type*: boolean
    | *Default*: `null`
    | *Options*

       - ``true``
       - ``false``

``scaling_policy``
******************

Defines scaling policy to attach to ASG. If this block does not exist, no scaling policy will be attached

``scaling_policy`` *Keys*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        ``metrics`` : The metrics to use for auto-scaling.

            | *Default*: ``"CPUUtilization"```
            | *Options*:

               - ``"CPUUtilization"``
               -  ``"NetworkIn"``
               -  ``"NetworkOut"``
               -  ``"DiskReadBytes"``

        ``threshold`` : Metrics value limit for scaling up

            | *Type*: int

        ``period_minutes`` : Time period to look across for determining if threshold was met

            | *Type*: int
            | *Units*: Minutes

        ``statistic``: Statistic to calculate at the period to determine if threshold was met

            | *Default*: ``"Average"``
            | *Options*:

               - ``"Average"``
               - ``"Maximum"``
               - ``"Minimum"``
               - ``"Sum"``

``scaling_policy`` *Example*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

      "scaling_policy": {
          "metric": "CPUUtilization",
          "threshold": 90,
          "period_minutes": 10,
          "statistic": "Average"
          }

``elb`` Block
~~~~~~~~~~~~~~

Top level key for ELB configuration

``access_log``
**************

Access Log configuration block. Ensure S3 bucket has proper bucket policy to enable writing.

``access_log`` *Keys*
^^^^^^^^^^^^^^^^^^^^^

    ``bucket_name`` : Name of S3 bucket to write access log to

        | *Type*: string
        | *Default*: Null

    ``bucket_prefix`` : Prefix to write to in the S3 bucket

        | *Type*: string
        | *Default*: Null

    ``emit_interval`` : ELB Access Log write delay

        | *Type*: int
        | *Range*: 5-60
        | *Units*: seconds
        | *Default*: Null

``connection_draining_timeout``
*******************************

Connection Draining Timeout to set on the ELB. This allows existing requests to complete before the load balancer shifts traffic away from a deregistered or unhealthy instance.

    | *Type*: int
    | *Range*: 1-3600
    | *Units*: seconds
    | *Default*: Null

``certificate``
***************

Name of SSL certification for ELB. SSL certificate must be uploaded to AWS first

    | *Default*: Null

``health``
**********

Health check configuration block

``health`` *Keys*
^^^^^^^^^^^^^^^^^^^^^

    ``interval`` : ELB health check interval

        | *Type*: int
        | *Units*: seconds
        | *Default*: ``20``

    ``threshold`` : Number of consecutive health check succeses before declaring EC2 instance healthy.

        | *Default*: ``2``

    ``timeout`` : Health check response timeout

        | *Type*: int
        | *Units*: seconds
        | *Default*: ``10``

    ``unhealthy_threshold`` : number of consecutive health check failures before declaring EC2 instance unhealthy

        | *Default*: ``5``

``idle_timeout``
****************

Idle Timeout to set on the ELB. This the time, in seconds, that the connection is allowed to be idle (no data has been sent over the connection) before it is closed by the load balancer.

    | *Type*: int
    | *Range*: 1-3600
    | *Units*: seconds
    | *Default*: 60

``ports``
*********

Defines ELB listeners. Expects a list of listeners.

``ports`` *Keys*
^^^^^^^^^^^^^^^^^^^^

    ``instance`` : The protocol:port of the instance

        | *Default*: ``"HTTP:8080"``

    ``loadbalancer`` : the protocol:port of the load balancer

        | *Default*: ``"HTTP:80"``

    ``stickiness`` : defines stickiness on ELB; if app, specify cookie_name, if elb, specify cookie_ttl

        | *Default*: ``None``

        | *Supported Types*: ``elb``, ``app``

        | *Example*:

            ::

                "stickiness": {
                    "type": "app",
                    "cookie_name": "$cookiename"
                }

                "stickiness": {
                    "type": "elb",
                    "cookie_ttl": 300
                }


    ``certificate`` : The name of the certificate to use if required

        | *Default*: ``null``

    ``listener_policies`` : A list of listener policies to associate to an ELB. Must be created in AWS first.

        | *Default*: ``[]``

        | *Type*: List of strings

    ``backend_policies`` : A list of backend server policies to associate to an ELB. Must be created in AWS first.

        | *Default*: ``[]``
        | *Type*: List of strings
        | *Example*: ``["WebSocket-Proxy-Protocol"]```

``ports`` *Example*
^^^^^^^^^^^^^^^^^^^

::

    "ports": [
        {
          "instance": "HTTP:8080",
          "loadbalancer": "HTTP:80",
          "stickiness": {
            "type": "app",
            "cookie_name": "cookie"
          }
        },
        {
          "certificate": "my_cert",
          "instance": "HTTP:8443",
          "loadbalancer": "HTTPS:443",
          "listener_policies": ["MyExamplePolicy"],
          "stickiness": {
            "type": "elb",
            "cookie_name": 300
          }
        }
      ]

``subnet_purpose``
******************

Determines if the load balancer should be public (external) or non-public (internal).

    | *Default*: ``"internal"``
    | *Options*:

       - ``"internal"``
       - ``"external"``

``target``
***********

The check the ELB will use to validate application is online.

    | *Default*: ``"TCP:8080"``

``regions`` Key
~~~~~~~~~~~~~~~~

List of AWS regions that application will be deployed to.

    | *Type*: List of strings
    | *Default*: ``[ "us-east-1" ]``

``deploy_strategy`` Key
~~~~~~~~~~~~~~~~~~~~~~~~

Spinnaker strategy to use for deployments.

    | *Default*: "highlander"
    | *Options*:

       - ``"highlander"`` - destroy old server group
       - ``"redblack"`` - disables old server group but do not destroy

``security_group`` Block
~~~~~~~~~~~~~~~~~~~~~~~~

Hold configuration for creating application specific security group

``description``
***************

Description of the security group. Used in AWS for creation

    | *Default*: ``"Auto-Gen SG for {{ app }}"``

``elb_extras``
***************

A list of extra security groups to assign to ELB

    | *Type*: List of strings
    | *Default*: ``[]``
    | *Example*: ``["all_access", "test_sg"]```

``instance_extras``
*******************

A list of extra security groups to assign to each instance

    | *Type*: List of strings
    | *Default*: ``[]``
    | *Example*: ``["all_access", "test_sg"]```

``ingress``
***********

Provides a list of other security groups and ports to allow inbound access to application

``egress``
***********

Provides info about outbound access from application

    | *Default*: ``"0.0.0.0/0"```

``security_group`` *Example*
****************************

You can reference SG by name or by cidr block, you can also specify cross account SG by name by referring to the spinnaker environment name. To see an example of this see below:

::

    "security_group": {
        "ingress": {
            "examplesecuritygroupname": [
                { "start_port": 80, "end_port": 80, "protocol": "tcp" },
                { "start_port": 443, "end_port": 443, "protocol": "tcp" },
                { "start_port": 443, "end_port": 443, "protocol": "tcp", "env": "prod" },
            ],
            "192.168.100.0/24": [
                { "start_port": 80, "end_port": 80, "protocol": "tcp" }
            ]
        },
        "egress": {
            "192.168.100.0/24": [
                { "start_port": 80, "end_port": 80, "protocol": "tcp" }
            ]
        }
    }

``dns`` Block
~~~~~~~~~~~~~~

Top level key for dns settings

``ttl``
********

Defines DNS TTL for generated DNS records

    | *Type*: int
    | *Units*: seconds
    | *Default*: ``60``

.. _lambda_trigger:

``lambda_triggers``
~~~~~~~~~~~~~~~~~~~

A list of all events to trigger a Lambda function. See :ref:`lambda_events` for details

    | *Type*: List
    | *Default*: ``[]``
