.. _application_json:

================================
application-master-$account.json
================================

.. contents::
   :local:

Purpose
-------

This configuration file holds infrastruction information for $account. Each AWS
account in your pipeline would need a seperate application-master-$account.json
file. If your account is named dev, you would want an
application-master-dev.json file.

Example Configuration
---------------------

.. literalinclude:: ../../src/foremast/templates/configs/configs.json.j2

Configuration Details
---------------------

``app`` Block
~~~~~~~~~~~~~

Top level key that contains information on the application and EC2 details

``app_description``
*******************

Describes the application.

    | *Type*: string
    | *Default*: ``null``

``approval_skip``
*****************

Enable the ability to skip approval stage for a given environment. Must be enabled in foremast configs per environment to allow overrides.

    | *Type*: boolean
    | *Default*: ``false``

``approval_timeout``
*******************

Enable the ability to override Spinnaker's default Stage Timeout (typically 72-hours) with a custom timeout specified in milliseconds.
This is helpful to maintain cleaner pipelines, and fail pipelines not ready for the next environment.
For example, ``2 hours`` is represented as ``7200000``.

    | *Type*: int
    | *Format*: ms
    | *Default*: ``null``

.. _archaius_enabled:

``archaius_enabled``
******************

Setting this value to ``true`` will autocreate archiaus pathing in
a specified archaius S3 bucket.

    | *Type*: boolean
    | *Default*: ``false``

``custom_tags``
***************

Custom Tags to be used during deployment stages on resources such as ELBs and EC2s.

``custom_tags`` *Example*
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: json

   {
       "app": {
            "custom_tags": {
                "example_key": "example_value",
                "app_name": "application_name"
            }
       }
   }

.. _eureka_enabled:

``eureka_enabled``
******************

Setting this value to ``true`` will not create an ELB, DNS record, and set the
ASG health check to EC2.

    | *Type*: boolean
    | *Default*: ``false``

``instance_profile``
********************

The instance profile to start EC2 instances with. Foremast creates default
instance profile based on the default string. Specifying a different profile
name assumes the profile exists.

    | *Type*: string
    | *Default*: ``"${group}_${app}_profile"``

``instance_type``
*****************

The size/type of the EC2 instance. Uses Standard AWS instance names. See
https://aws.amazon.com/ec2/instance-types/ for details

    | *Type*: string
    | *Default*: ``"t2.micro"``

``lambda_concurrency_limit``
****************************

Each region in your AWS account has a Lambda concurrency limit. The concurrency limit determines how many function invocations can run simultaneously in one region. The limit applies to all functions in the same region and is set to 1000 by default.

If you exceed a concurrency limit, Lambda starts throttling the offending functions by rejecting requests. Depending on the invocation type, you’ll run into the following situations:

More info on limits can be found here: https://docs.aws.amazon.com/lambda/latest/dg/limits.html

``lambda_destinations``
***********************

This feature provides the ability to control what happens when a function is successful or fails e.g. if a specific function fails you may want to invoke another lambda function to perform some error management. In the past you would have to add this bespoke functionality into your code. 

Destinations currently support following:
* ARN of Lambda Function
* ARN of SQS Queue
* ARN of SNS Topic
* ARN of Amazon EventBridge event bus

You may either an individual destination path OR one for both success and failure. 

More details on lambda destinations can be found here: https://aws.amazon.com/blogs/compute/introducing-aws-lambda-destinations/

    | *Type*: Object
    | *Default*: ``{}``

``lambda_destinations`` *Example*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: json

   "lambda_destinations": {
    "OnSuccess": { "Destination": "arn"},
    "OnFailure": { "Destination": "arn"}
    }



``lambda_dlq``
*****************

A dead letter queue configuration that specifies the queue or topic where Lambda sends asynchronous events when they fail processing 

Dead Letter Queues are supported in either SNS or SQS and pass in the ARN. See https://docs.aws.amazon.com/lambda/latest/dg/invocation-async.html for more details

    | *Type*: Object
    | *Default*: ``{}``

``lambda_dlq`` *Example*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: json

   "lambda_dlq": {
            "TargetArn": "arn:aws:sns:us-east-1:accountnumber:topic"
        }


``lambda_environment``
**********************

Environment variables which are passed to the lambda function.

``lambda_environment`` *Keys*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    ``Variables`` : Dictionary of environment variables.

        | *Type*: object
        | *Default*: ``null``

``lambda_environment`` *Example*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: json

   {
       "lambda_environment": {
           "Variables": {
               "VAR1": "val1",
               "VAR2": "val2",
               "VAR3": "val3"
           }
       }
   }

``lambda_filesystems``
*****************

List of Dictionaries that are passed with the EFS filesystem configuration. 
Expects the ARN of the filesystem and the Local Mount Path

    | *Type*: list
    | *Default*: ``[]``

``lambda_filesystems`` *Example*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: json

   {
    "Arn": "arn",
    "LocalMountPath": "/mnt/efs/"
   }


``lambda_layers``
*****************

List of AWS Lambda Layer ARNs to add to Lambda Function

    | *Type*: list
    | *Default*: ``[]``

``lambda_memory``
*****************

The amount of memory to give a Lambda function

    | *Type*: string
    | *Default*: ``"128"``
    | *Units*: Megabytes

``lambda_provisioned_throughput``
***********************

This will allow provisioned throughput of a  lambda function. This specifically will ensure the function is warmed for a provisioned amount to eliminate any function cold starts (not to be confused with VPC cold starts)

More info on provisioned throughput can be found here: https://aws.amazon.com/blogs/aws/new-provisioned-concurrency-for-lambda-functions/

    | *Type*: int
    | *Default*: ``null``
    
``lambda_role``
***************

Override the default generated IAM Role name.

    | *Type*: string
    | *Default*: ``"${group}_${app}_role"``

``lambda_subnet_count``
***********************

Enables ablity to specify subnet resiliency of lambda functions. By default, uses all subnets of type ``subnet_purpose`` specified.

Each VPC in your AWS account has a Hyperplane ENI limit. The ENI Limit determines how many Hyperplane ENIs you can have in one VPC. The limit applies to Lambda in the same VPC and is set to 250 by default. If you exceed a ENI Limit, Lambda deployment will fail with a Hyperplane ENI Limit error. 

At this time, you will need to submit a limit increase or reduce how many SG:Subnet Tuples you have per function. When you connect a function to a VPC, Lambda creates an elastic network interface for each combination of security group and subnet in your function's VPC configuration.

More info on limits can be found here: https://docs.aws.amazon.com/lambda/latest/dg/limits.html

    | *Type*: int
    | *Default*: ``<<MAX SUBNET COUNT>>``

``lambda_timeout``
******************

The timeout setting for Lambda function. See official limits
https://docs.aws.amazon.com/lambda/latest/dg/limits.html

    | *Type*: string
    | *Default*: ``"900"``
    | *Units*: Seconds

``lambda_tracing``
******************

Lambda Tracing feature allows you to enable X-Ray APIs to your lambda function to identify performance bottlenecks and troubleshoot requests that are in error. 

If you've enabled X-Ray tracing in a service that invokes your function, Lambda sends traces to X-Ray automatically. The upstream service, such as Amazon API Gateway, or an application hosted on Amazon EC2 that is instrumented with the X-Ray SDK, samples incoming requests and adds a tracing header that tells Lambda to send traces or not. For a full list of services that support active instrumentation, see Supported AWS Services in the AWS X-Ray Developer Guide. For more details see: https://docs.aws.amazon.com/lambda/latest/dg/lambda-x-ray.html

Currently AWS API supports Active or PassThrough.

    | *Type*: Object
    | *Default*: ``{}``

``lambda_tracing`` *Example*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: json

   "lambda_tracing": {
            "Mode": "Active"
        }

``cloudfunction_timeout``
**********************

The function execution timeout. Execution is considered failed and can be terminated if the function is not completed at the end of the timeout period. Defaults to 60 seconds.

A duration in seconds with up to nine fractional digits, terminated by 's'. Example: "3.5s".

    | *Type*: String
    | *Default*: ``None``
    | *Example*: ``"60s"``

``cloudfunction_memory_mb``
**********************

Memory in Mb specified as an integer (without Mb or mb after the value).  GCP currently defaults to 256Mb if no value is given.

    | *Type*: Integer
    | *Default*: ``None``
    | *Example*: ``128``

``cloudfunction_environment``
**********************

Environment variables that should be present when the Cloud Function is invoked.

    | *Type*: Dictionary
    | *Default*: ``None``
    | *Example*: ``{ 'MY_ENV_VAR': 'My value!' }``

``cloudfunction_allow_unauthenticated``
**********************

Creates an IAM Binding which will allow anonymous/unauthenticated users to invoke the function. This only applies to
HTTP triggers, event triggers cannot be invoked by users directly.  This option mimics the ``gcloud functions deploy ... --allow-unauthenticated`` CLI option and
adds an IAM binding for 'allUsers' with 'roles/cloudfunctions.invoker'.

    | *Type*: Boolean
    | *Default*: ``False``

``cloudfunction_iam_bindings``
**********************

Updates the Cloud Function's IAM Policy, which can be used to control which users or service accounts can access the function.  It allows granular control
on who has permissions to the function, and not which permissions the function itself has.  For allowing anonymous access to the function the
``cloudfunction_allow_unauthenticated=True`` option is simpler.

    | *Type*: Array
    | *Default*: ``[]``
    | *Example*:

        .. code-block:: json

            [
              {
                "members": [
                    "user:jon.snow@GameOfThrones.com",
                    "serviceAccount:my-service-acccount@my-project.iam.gserviceaccount.com",
                ],
                "role": "roles/cloudfunctions.invoker"
              }
            ]

.. note::

   The role `roles/cloudfunctions.invoker` does not allow invoking via ``gcloud functions call ...``, instead use a command like
    ``curl $URL -H "Authorization: bearer $(gcloud auth print-identity-token)`` to test granular invocation permissions

``cloudfunction_max_instances``
**********************

Maximum number of instances of a function that can run in parallel.  GCP defaults to no limit if a value is not given.

    | *Type*: Integer
    | *Default*: ``None``
    | *Example*: ``5``

``cloudfunction_ingress_type``
**********************

Ingress type to use.  Foremast does not have a default, however GCP Defaults to ``ALLOW_ALL`` if none is given.
Options are: ``INGRESS_SETTINGS_UNSPECIFIED``, ``ALLOW_ALL``, ``ALLOW_INTERNAL_ONLY``, ``ALLOW_INTERNAL_AND_GCLB``

For information on this option see the `GCP Documentation on Ingress Settings <https://cloud.google.com/functions/docs/reference/rest/v1/projects.locations.functions#ingresssettings>`_.

    | *Type*: String
    | *Default*: ``None``
    | *Example*: ``ALLOW_INTERNAL_ONLY``

``cloudfunction_vpc``
**********************

.. code-block:: json

   "cloudfunction_vpc": {
      "connector": {
        "us-central1": "projects/your-vpc-project/locations/us-central1/connectors/stage-us-central1",
        "us-east1": "projects/your-vpc-project/locations/us-east1/connectors/stage-us-east1"
      },
      "egress_type": "PRIVATE_RANGES_ONLY"
    }

``connector``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

VPC Connector to use, which will allow private VPC network access to the Cloud Function.  Should be defined
as key/value pairs where the key is the region and the value is the VPC connector.

    | *Type*: Dictionary
    | *Default*: ``None``
    | *Example*:

        .. code-block:: json

             {
                "us-central1":  "projects/your-host-project/locations/us-central1/connectors/yourconnector-us-central1",
                "us-east1":     "projects/your-host-project/locations/us-east1/connectors/yourconnector-us-east1"
             }

``egress_type``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Egress type to use.  Foremast does not have a default, however GCP Defaults to ``PRIVATE_RANGES_ONLY`` if none is given.
Options are: ``VPC_CONNECTOR_EGRESS_SETTINGS_UNSPECIFIED``, ``PRIVATE_RANGES_ONLY``, ``ALL_TRAFFIC``.

For information on this option see the  `GCP Documentation on VPC Egress Settings <https://cloud.google.com/functions/docs/reference/rest/v1/projects.locations.functions#VpcConnectorEgressSettings>`_.

    | *Type*: String
    | *Default*: ``None``
    | *Example*: ``PRIVATE_RANGES_ONLY``

``cloudfunction_event_trigger``
**********************************

Configures a trigger for a GCP Cloud Function.  If none is given, GCP will default to an HTTPS trigger.  Trigger
types are immutable in GCP, so once a trigger type is used (https, pub/sub, GCS, etc) it cannot be changed.  It
is possible to change the resource used in the trigger, but not the trigger type itself.


    | *Example Pub/Sub trigger*:

        .. code-block:: json

           "cloudfunction_event_trigger": {
              "event_type": "providers/cloud.pubsub/eventTypes/topic.publish",
              "resource": "/topics/my_topic",
              "failure_policy": {
                "retry": true
              }
            }

    | *Example GCS Bucket trigger*:

        .. code-block:: json

           "cloudfunction_event_trigger": {
              "resource": "buckets/my_bucket_name",
              "event_type": "google.storage.object.archive",
              "failure_policy": {
                "retry": false
              }
            }

``event_type``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Event type to trigger the Cloud Function.  Event types and their formats can vary, the easiest way to determine
your event type is to run the command `gcloud functions event-types list <https://cloud.google.com/sdk/gcloud/reference/functions/event-types/list>`_. and refer to the EVENT_TYPE column.

    | *Type*: String
    | *Default*: ``None``
    | *Example Pub/Sub*: ``providers/cloud.pubsub/eventTypes/topic.publish``
    | *Example Storage*: ``google.pubsub.topic.publish``
    | *Example Firestore Storage*: ``providers/cloud.firestore/eventTypes/document.write``

``resource``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The resource to trigger off of.  The resource type given must match the ``event_type`` specified.  For example, a resource
path to a GCS Bucket with a Pub/Sub event trigger will be rejected.  GCP expects the project to be specified and the
full path to the resource, however if omitted Foremast will add this automatically.

    | *Type*: String
    | *Default*: ``None``
    | *Example Pub/Sub*: ``topics/my_topic``
    | *Example Storage*: ``buckets/my_bucket``



``asg`` Block
~~~~~~~~~~~~~

Top level key containing information regarding application ASGs

``hc_type``
************

.. note::

   See
   :func:`foremast.pipeline.construct_pipeline_block.construct_pipeline_block`
   for cases where the Health Check type is overridden to ``"EC2"``.

ASG Health check type (EC2 or ELB)

    | *Type*: string
    | *Default*: ``"ELB"``
    | *Options*:

       - ``"ELB"``
       - ``"EC2"``

``app_grace_period``
********************

App specific health check grace period (added onto default ASG healthcheck grace
period) to delay sending of health check requests. This is useful in the event
your application takes longer to boot than the default hc_grace_period defined
in templates.

For example, hc_grace_period may be 180 seconds, but an app may need a variable
amount of time to boot (say 30 seconds extra). This will add 180 + 30 to
calculate the overall hc_grace_period of 210 seconds.

    | *Type*: number
    | *Default*: ``0``
    | *Units*: Seconds

``max_inst``
************

Maximum number of instances ASG will scale to.

    | *Type*: number
    | *Default*: ``3``

``min_inst``
************

Minimum number of instances your auto-scaling group should have at all times.
This is also the default number of instances

    | *Type*: number
    | *Default*: ``1``

``ssh_keypair``
***************

SSH key that your EC2 instances will use. Must already be created in AWS. This
replaces the non-functional and deprecated app_ssh_key configuration key.

    | *Type*: string
    | *Default*: ``"{{ account }}_{{ region }}_default"`` - {{ account }} being
      the AWS account in the configuration name

``subnet_purpose``
******************

Determines if the instances should be public (external) or non-public
(internal).

    | *Type*: string
    | *Default*: ``"internal"``
    | *Options*

       - ``"internal"``
       -  ``"external"``

``enable_public_ips``
*********************

Determines if instances in an cluster should have public IPs associated. By
default, this is set to null which means it uses default behavior configured for
your subnets in your cloud provider.

    | *Type*: boolean
    | *Default*: `null`
    | *Options*

       - ``true``
       - ``false``

``scaling_policy``
******************

To better explain this feature, this has has been moved to: :doc:`advanced_usages/scaling_policy`

``custom_scaling_policies``
***************************

To better explain this feature, this has has been moved to: :doc:`advanced_usages/custom_scaling_policies`

``scheduled_actions``
*********************

To better explain this feature, this has has been moved to: :doc:`advanced_usages/scheduled_actions`

``elb`` Block
~~~~~~~~~~~~~

Top level key for ELB configuration

``access_log``
**************

Access Log configuration block. Ensure S3 bucket has proper bucket policy to
enable writing.

``access_log`` *Keys*
^^^^^^^^^^^^^^^^^^^^^

    ``bucket_name`` : Name of S3 bucket to write access log to

        | *Type*: string
        | *Default*: Null

    ``bucket_prefix`` : Prefix to write to in the S3 bucket

        | *Type*: string
        | *Default*: Null

    ``emit_interval`` : ELB Access Log write delay

        | *Type*: number
        | *Range*: 5-60
        | *Units*: seconds
        | *Default*: Null

``connection_draining_timeout``
*******************************

Connection Draining Timeout to set on the ELB. This allows existing requests to
complete before the load balancer shifts traffic away from a deregistered or
unhealthy instance.

    | *Type*: number
    | *Range*: 1-3600
    | *Units*: seconds
    | *Default*: Null

``certificate``
***************

Name of SSL certification for ELB. SSL certificate must be uploaded to AWS
first.

    | *Type*: string
    | *Default*: Null

``health``
**********

Health check configuration block

``health`` *Keys*
^^^^^^^^^^^^^^^^^

``interval`` : ELB health check interval

   | *Type*: number
   | *Units*: seconds
   | *Default*: ``20``

``threshold`` : Number of consecutive health check succeses before declaring EC2
instance healthy.

   | *Type*: number
   | *Default*: ``2``

``timeout`` : Health check response timeout

   | *Type*: number
   | *Units*: seconds
   | *Default*: ``10``

``unhealthy_threshold`` : number of consecutive health check failures before
declaring EC2 instance unhealthy

   | *Type*: number
   | *Default*: ``5``

``idle_timeout``
****************

Idle Timeout to set on the ELB. This the time, in seconds, that the connection
is allowed to be idle (no data has been sent over the connection) before it is
closed by the load balancer.

    | *Type*: number
    | *Range*: 1-3600
    | *Units*: seconds
    | *Default*: 60

``ports``
*********

Defines ELB listeners. Expects a list of listeners.

``ports`` *Keys*
^^^^^^^^^^^^^^^^

``instance`` : The protocol:port of the instance

   | *Type*: string
   | *Default*: ``"HTTP:8080"``

``loadbalancer`` : the protocol:port of the load balancer

   | *Type*: string
   | *Default*: ``"HTTP:80"``

``stickiness`` : defines stickiness on ELB; if app, specify cookie_name, if elb,
specify cookie_ttl

   | *Type*: object
   | *Default*: ``None``
   | *Supported Types*: ``elb``, ``app``
   | *Example app*:

      .. code-block:: json

         {
             "stickiness": {
                 "type": "app",
                 "cookie_name": "$cookiename"
             }
         }

   | *Example elb*:

      .. code-block:: json

         {
             "stickiness": {
                 "type": "elb",
                 "cookie_ttl": 300
             }
         }

``certificate`` : The name of the certificate to use if required

   | *Type*: string
   | *Default*: ``null``

``listener_policies`` : A list of listener policies to associate to an ELB. Must
be created in AWS first.

   | *Type*: array
   | *Default*: ``[]``

``backend_policies`` : A list of backend server policies to associate to an ELB.
Must be created in AWS first.

   | *Type*: array
   | *Default*: ``[]``
   | *Example*: ``["WebSocket-Proxy-Protocol"]```

``ports`` *Example*
^^^^^^^^^^^^^^^^^^^

.. code-block:: json

   {
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
               "listener_policies": [
                   "MyExamplePolicy"
               ],
               "stickiness": {
                   "type": "elb",
                   "cookie_name": 300
               }
           }
       ]
   }

``subnet_purpose``
******************

Determines if the load balancer should be public (external) or non-public
(internal). When changing this option, the ELB and DNS Records must be manually
destroyed before deployment. This is necessary because the ELB Scheme is not
modifiable.

    | *Type*: string
    | *Default*: ``"internal"``
    | *Options*:

       - ``"internal"``
       - ``"external"``

``target``
**********

The check the ELB will use to validate application is online.

    | *Type*: string
    | *Default*: ``"TCP:8080"``

``regions`` Key
~~~~~~~~~~~~~~~

Dictionary of AWS regions that application will be deployed to.

    | *Type*: array
    | *Default*: ``{ "us-east-1": {} }``

``deploy_strategy`` Key
~~~~~~~~~~~~~~~~~~~~~~~

Spinnaker strategy to use for deployments.

    | *Type*: string
    | *Default*: "highlander"
    | *Options*:

       - ``"highlander"`` - destroy old server group
       - ``"redblack"`` - disables old server group but do not destroy
       - ``"canary"`` - Only used in S3 deployments. Causes pipeline to first
         deploy to CANARY path
       - ``"alpha"`` - Only used in S3 deployments. Causes pipeline to first
         deploy to an ALPHA path
       - ``"mirror"`` - Only used in S3 deployments. Contents are deployed
         as-is, no version or LATEST directory
       - ``"branchrelease"`` - Only used in S3 deployments. S3 Folders coorelate to 
         Git Branches, using versions and LATEST directory

``security_group`` Block
~~~~~~~~~~~~~~~~~~~~~~~~

Hold configuration for creating application specific security group

``description``
***************

Description of the security group. Used in AWS for creation

    | *Type*: string
    | *Default*: ``"Auto-Gen SG for {{ app }}"``

``elb_extras``
**************

A list of extra security groups to assign to ELB

    | *Type*: array
    | *Default*: ``[]``
    | *Example*: ``["all_access", "test_sg"]```

``instance_extras``
*******************

A list of extra security groups to assign to each instance

    | *Type*: array
    | *Default*: ``[]``
    | *Example*: ``["all_access", "test_sg"]```

``ingress``
***********

Provides a list of other security groups and ports to allow inbound access to
application

``egress``
**********

Provides info about outbound access from application

    | *Type*: string
    | *Default*: ``"0.0.0.0/0"```

``security_group`` *Example*
****************************

You can reference SG by name or by cidr block, you can also specify cross
account SG by name by referring to the spinnaker environment name. To see an
example of this see below:

.. code-block:: json

   {
       "security_group": {
           "ingress": {
               "examplesecuritygroupname": [
                   {"start_port": 80, "end_port": 80, "protocol": "tcp"},
                   {"start_port": 443, "end_port": 443, "protocol": "tcp"},
                   {"start_port": 443, "end_port": 443, "protocol": "tcp", "env": "prod"}
               ],
               "192.168.100.0/24": [
                   {"start_port": 80, "end_port": 80, "protocol": "tcp"}
               ]
           },
           "egress": {
               "192.168.100.0/24": [
                   {"start_port": 80, "end_port": 80, "protocol": "tcp"}
               ]
           }
       }
   }

``dns`` Block
~~~~~~~~~~~~~

Top level key for dns settings

``ttl``
*******

Defines DNS TTL for generated DNS records

    | *Type*: number
    | *Units*: seconds
    | *Default*: ``60``

.. _lambda_trigger:

``lambda_triggers``
~~~~~~~~~~~~~~~~~~~

A list of all events to trigger a Lambda function. See :ref:`lambda_events` for
details

    | *Type*: array
    | *Default*: ``[]``

.. include:: datapipeline.rest

.. include:: s3.rest

.. include:: stepfunction.rest

.. include:: qe.rest


``completion_webhooks`` *Example*
****************************

Completion Webhooks are Spinnaker Webhook Stages that are appended to the pipeline stages
for this environment.

.. code-block:: json

   {
       "completion_webhooks": [
          {
            "url": "https://webhook.com/webhook1",
            "custom_headers": {
              "my-header": "hello"
            },
            "method": "POST",
            "name": "Webhook 1",
            "payload": {
              "webhook": "one"
            }
          },
          {
            "url": "https://webhook.com/webhook2",
            "custom_headers": {
              "my-header": "hello again"
            },
            "method": "POST",
            "name": "Webhook 2",
            "payload": {
              "webhook": "two"
            }
          }
       ]
   }
