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

.. literalinclude:: ../src/foremast/templates/configs.json.j2

Configuration Details
----------------------

``app`` Block
~~~~~~~~~~~~~

Top level key that contains information on the application and EC2 details

``app_description``
************************

Describes the application.

    | *Default*: ``null``

``app_ssh_key``
*******************

SSH key that your EC2 instances will use. Must already be created in AWS.

    | *Default*: ``"{{ account }}_access"`` - {{ account }} being the AWS account in the configuration name

``eureka_enabled``
***********************

Setting this value to true will not create an ELB, DNS record, and set the ASG health check to EC2.

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

``subnet_purpose``
******************

Determines if the instances should be public (external) or non-public (internal).

    | *Default*: ``"internal"``
    | *Options*

       - ``"internal"``
       -  ``"external"``

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

``ports``
*********

Defines ELB listeners. Expects a list of listeners.

``ports`` *Keys*
^^^^^^^^^^^^^^^^^^^^

    ``instance`` : The protocol:port of the instance

        | *Default*: ``"HTTP:8080"``

    ``loadbalanacer`` : the protocol:port of the load balancer

        | *Default*: ``"HTTP:80"``

    ``certificate`` : The name of the certificate to use if required

        | *Default*: ``null``

``ports`` *Example*
^^^^^^^^^^^^^^^^^^^

::

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

``dns`` Block
~~~~~~~~~~~~~~

Top level key for dns settings

``ttl``
********

Defines DNS TTL for generated DNS records

    | *Type*: int
    | *Units*: seconds
    | *Default*: ``60``
