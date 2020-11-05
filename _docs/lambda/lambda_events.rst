.. _lambda_events:

##########################
Lambda Triggers and Events
##########################

Foremast supports multiple Lambda events. These are configured in the :ref:`application_json` config and set as a list under the :ref:`lambda_trigger` key.

.. contents::
   :local:

Example Configuration
*********************

This example would go in the :ref:`application_json` configuration file.

.. code-block:: json

   {
     "lambda_triggers": [
       {
         "type": "api-gateway",
         "api_name": "lambdatest-api",
         "resource": "/index",
         "method": "GET"
       },
       {
         "type": "cloudwatch-event",
         "rule_name": "app cron - 5min",
         "rule_type": "schedule",
         "rule_description": "triggers lambda function every five minutes",
         "schedule": "rate(5 minutes)"
       },
       {
         "type": "cloudwatch-event",
         "rule_name": "GuardDutyEvents",
         "rule_type": "event_pattern",
         "rule_description": "Trigger Lambda Function for every AWS GuardDutyEvent",
         "event_pattern": {"source": ["aws.guardduty"]}
       },
       {
         "type": "cloudwatch-logs",
         "log_group": "/aws/lambda/awslimit_test",
         "filter_name": "Trigger lambda on every WARNING message",
         "filter_pattern": ""
       },
       {
         "type": "dynamodb-stream",
         "table_arn": "arn:aws:dynamodb:us-east-1:111111111111:table/dynamotest-stream",
         "stream_arn": "",
         "batch_size": 100,
         "batch_window": 0,
         "starting_position": "TRIM_HORIZON",
         "max_retry": 3000,
         "split_on_error": true,
         "destination_config":{
         "OnFailure": {
            "Destination":"arn:aws:sns:us-east-1:111111111111:snstest-queue"
            }
         }
       },
       {
         "type": "kinesis-stream",
         "stream_arn": "arn:aws:kinesis:us-east-1:111111111111:stream/kinesistest-stream",
         "batch_size": 100,
         "batch_window": 0,
         "parallelization_factor": 1,
         "starting_position": "TRIM_HORIZON",
         "starting_position_timestamp": 1604617998,
         "split_on_error": true,
         "max_retry": 3000,
         "destination_config": {
           "OnFailure": {
             "Destination": "arn:aws:sqs:us-east-1:111111111111:sqstest-queue"
           }
         }
       },
       {
         "type": "s3",
         "bucket": "app-bucket-dev",
         "events": [
           "s3:ObjectCreated:*"
         ],
         "prefix": "",
         "suffix": ""
       },
       {
         "type": "sns",
         "topic": "app-dns-dev"
       },
       {
         "type": "sqs",
         "queue_arn": "arn:aws:sqs:us-east-1:111111111111:sqstest-queue",
         "batch_size": 10
       }
     ]
   }

Configuration Details
*********************

``type``
========

    Specifies what type of Lambda event/trigger to use. This needs to be set for all events.

        | *Type*: string
        | *Required*: True
        | *Options*:

            - ``"api-gateway"`` - API Gateway Lambda trigger
            - ``"cloudwatch-event"`` - Cloudwatch Event Lambda trigger
            - ``"cloudwatch-logs"`` - Cloudwatch Logs Lambda trigger
            - ``"dynamodb-stream"`` - DynamoDB Stream Lambda trigger
            - ``"kinesis-stream"`` - Kinesis Stream Lambda trigger
            - ``"sns"`` - SNS Lambda trigger
            - ``"sqs"`` - SQS Queue Lambda trigger
            - ``"s3"`` - S3 Lambda trigger

``api-gateway`` Trigger *Keys*
==============================

Sets up an API Gatway event to trigger a lambda function.

``api_name``
^^^^^^^^^^^^

    The name of an existing API Gateway. If not provided, an API will be created.

        | *Type*: string
        | *Required*: False
        | *Default*: ``{app_name}``

``resource``
^^^^^^^^^^^^

    The API resource to tie the Lambda function to.

        | *Type*: string
        | *Required*: True
        | *Example*: ``"/test"``

``method``
^^^^^^^^^^

    The API Method to trigger the Lambda function.

        | *Type*: string
        | *Required*: True
        | *Example*: ``"GET"``

``api_type``
^^^^^^^^^^

    The API Type for the gateway integration.

        | *Type*: string
        | *Required*: False
        | *Default*: ``"AWS"``
        | *Values*:

            - ``"HTTP"``
            - ``"MOCK"``
            - ``"HTTP_PROXY"``
            - ``"AWS_PROXY"``

``cloudwatch-event`` Event Pattern Trigger *Keys*
=================================================

A CloudWatch event pattern for Lambda triggers.

``rule_name``
^^^^^^^^^^^^^

    The name of the CloudWatch rule being created.

        | *Type*: string
        | *Required*: True

``rule_type``
^^^^^^^^^^^^^

    Type of CloudWatch Rule to create, must be set to ``"event_pattern"`` for Event Pattern Triggers.

        | *Type*: string
        | *Required*: True
        | *Default*: ``"schedule"``
        | *Values*:

            - ``"schedule"``
            - ``"event_pattern"``

``rule_description``
^^^^^^^^^^^^^^^^^^^^

    Description of the rule being created.

        | *Type*: string
        | *Required*: False

``event_pattern``
^^^^^^^^^^^^^^^^^

    CloudWatch Rule Event Pattern JSON. Usage Help can be found using the CloudWatch Rule GUI or the Docs:
    https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/CloudWatchEventsandEventPatterns.html

        | *Type*: string
        | *Required*: True
        | *Examples*:

            - ``{"source": ["aws.guardduty"]}``
            - ``{"source": [ "aws.ec2" ], "detail-type": ["EC2 Instance State-change Notification"], "detail": {"state": ["running"]}}``

``cloudwatch-event`` Schedule Trigger *Keys*
============================================

A CloudWatch Scheduled event for Lambda triggers.

``rule_name``
^^^^^^^^^^^^^

    The name of the CloudWatch rule being created.

        | *Type*: string
        | *Required*: True

``rule_type``
^^^^^^^^^^^^^

    Type of CloudWatch Rule to create

        | *Type*: string
        | *Required*: False
        | *Default*: ``"schedule"``
        | *Values*:

            - ``"schedule"``
            - ``"event_pattern"``

``rule_description``
^^^^^^^^^^^^^^^^^^^^

    Description of the rule being created.

        | *Type*: string
        | *Required*: False

``schedule``
^^^^^^^^^^^^

    The rate or cron string to trigger the Lambda function.

        | *Type*: string
        | *Required*: True
        | *Examples*:

            - ``"rate(5 minutes)"``
            - ``"cron(0 17 ? * MON-FRI *)"``

``cloudwatch-logs`` Trigger *Keys*
==================================

A lambda event that triggers off a Cloudwatch log action.

``log_group``
^^^^^^^^^^^^^

    The name of the log group to monitor.

        | *Type*: string
        | *Required*: True
        | *Example*: ``"/aws/lambda/test_function"``

``filter_name``
^^^^^^^^^^^^^^^

    The name of the filter on log event.

        | *Type*: string
        | *Required*: True

``filter_pattern``
^^^^^^^^^^^^^^^^^^

    The pattern to look for in the ``log_group`` for triggering a Lambda function.

        | *Type*: string
        | *Required*: True
        | *Example*: ``"warning"``

``dynamodb-stream`` Trigger *Keys*
==================================

    A lambda event that triggers off a DynamoDB Stream. 

    .. warning:: Ensure IAM Role has permissions to the DynamoDB table/stream via ``"services"`` block
    
    .. info:: If both ``stream_arn`` and ``table_arn`` keys are present, default behavior uses ``stream_arn`` as it is more specific.

``stream_arn``
^^^^^^^^^^^^^^

    DynamoDB Stream ARN to use for triggering lambda.

        | *Type*: string
        | *Required*: True, if ``table_arn`` is not set.
        | *Example*: ``"arn:aws:dynamodb:us-east-1:111111111111:table/foremast-test/stream/2018-06-07T03:12:22.234"``

``table_arn``
^^^^^^^^^^^^^

    DynamoDB Table ARN to use for triggering lambda. 
    
    .. info:: If specified, Foremast will lookup and use the latest Stream ARN.

        | *Type*: string
        | *Required*: True, if ``stream_arn`` is not set.
        | *Example*: ``"arn:aws:dynamodb:us-east-1:111111111111:table/foremast-test"``

``batch_size``
^^^^^^^^^^^^^^

    The maximum number of items to retrieve in a single batch.

        | *Type*: int
        | *Required*: False
        | *Default*: ``100``
        | *Max*: ``1000``

``batch_window``
^^^^^^^^^^^^^^^^

    The maximum amount of time to gather records before invoking the function, in seconds.

        | *Type*: int
        | *Required*: False
        | *Default*: ``0``
        | *Max*: ``300``

``parallelization_factor``
^^^^^^^^^^^^^^^^^^^^^^^^^^

    For Kinesis Streams, the number of batches to process from each shard concurrently.

        | *Type*: int
        | *Required*: False
        | *Default*: ``1``

``starting_position``
^^^^^^^^^^^^^^^^^^^^^

    The position in a stream from which to start reading.

        | *Type*: string
        | *Required*: False
        | *Default*: ``TRIM_HORIZON``
        | *Options*:

            -  ``TRIM_HORIZON``
            -  ``AT_TIMESTAMP`` - KINESIS STREAMS ONLY
            -  ``LATEST``

``starting_position_timestamp``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The UTC timestamp (represented in `Epoch Time <https://www.epochconverter.com>`_) from which to start reading..

        | *Type*: int
        | *Required*: False
        | *Default*: ``None``

``max_retry``
^^^^^^^^^^^^^^^^^^^^^

    Skips retrying a batch of records when it has reached the Maximum Retry Attempts.

        | *Type*: int
        | *Required*: False
        | *Default*: ``10000``
        | *Max*: ``10000``  

``split_on_error``
^^^^^^^^^^^^^^^^^^^^^

    Breaks the impacted batch of records into two when a function returns an error, and retries them separately.

        | *Type*: boolean
        | *Required*: False
        | *Default*: ``false``
        | *Options*:

            -  ``true``
            -  ``false``

``destination_config``
^^^^^^^^^^^^^^^^^^^^^

     Continue processing records after error, and send metadata of bad data record to an SQS queue or SNS topic.

        | *Type*: string
        | *Required*: False
        | *Default*: ````
        | *Options*:

            -  ``arn:aws:sqs:us-east-1:111111111111:sqstest-queue``
            -  ``arn:aws:sns:us-east-1:111111111111:snstest-queue``

``max_record_age``
^^^^^^^^^^^^^^^^^^^^^

    Maximum age of a record that is send to the function for processing.

        | *Type*: int
        | *Required*: False
        | *Default*: ``604800``
        | *Max*: ``604800`` 

``kinesis-stream`` Trigger *Keys*
=================================

    A lambda event that triggers off a Kinesis Stream. 
    
    .. warning:: Ensure IAM Role has permissions to the Kinesis Stream via ``"services"`` block

``stream_arn``
^^^^^^^^^^^^^^

    Kinesis Stream ARN to use for triggering lambda.

        | *Type*: string
        | *Required*: True
        | *Example*: ``"arn:aws:kinesis:us-east-1:111111111111:stream/kinesistest-stream"``

``batch_size``
^^^^^^^^^^^^^^

    The maximum number of items to retrieve in a single batch.

        | *Type*: int
        | *Required*: False
        | *Default*: ``100``
        | *Max*: ``10000``

``batch_window``
^^^^^^^^^^^^^^^^

    The maximum amount of time to gather records before invoking the function, in seconds.

        | *Type*: int
        | *Required*: False
        | *Default*: ``0``
        | *Max*: ``300``

``starting_position``
^^^^^^^^^^^^^^^^^^^^^

    The position in a stream from which to start reading.

        | *Type*: string
        | *Required*: False
        | *Default*: ``TRIM_HORIZON``
        | *Options*:

            -  ``TRIM_HORIZON``
            -  ``LATEST``

``max_retry``
^^^^^^^^^^^^^^^^^^^^^

    Skips retrying a batch of records when it has reached the Maximum Retry Attempts.

        | *Type*: int
        | *Required*: False
        | *Default*: ``10000``
        | *Max*: ``10000``  

``split_on_error``
^^^^^^^^^^^^^^^^^^^^^

    Breaks the impacted batch of records into two when a function returns an error, and retries them separately.

        | *Type*: boolean
        | *Required*: False
        | *Default*: ``false``
        | *Options*:

            -  ``true``
            -  ``false``

``destination_config``
^^^^^^^^^^^^^^^^^^^^^

     Continue processing records after error, and send metadata of bad data record to an SQS queue or SNS topic.

        | *Type*: string
        | *Required*: False
        | *Default*: ````
        | *Options*:

            -  ``arn:aws:sqs:us-east-1:111111111111:sqstest-queue``
            -  ``arn:aws:sns:us-east-1:111111111111:snstest-queue``

``max_record_age``
^^^^^^^^^^^^^^^^^^^^^

    Maximum age of a record that is send to the function for processing.

        | *Type*: int
        | *Required*: False
        | *Default*: ``604800``
        | *Max*: ``604800`` 

``s3`` Trigger *Keys*
=====================

A Lambda trigger on S3 bucket actions.

``bucket``
^^^^^^^^^^

    The bucket of the event to monitor.

        | *Type*: string
        | *Required*: True

``events``
^^^^^^^^^^

    The S3 event to trigger the lambda function from.

        | *Type*: List
        | *Required*: True
        | *Example*: ``["s3:ObjectCreated:*", "s3:ObjectedRemoved:Delete"]``

``prefix``
^^^^^^^^^^

    Sets up a prefix filter on S3 bucket events.

        | *Required*: False
        | *Example*: ``"logs/"``

``suffix``
^^^^^^^^^^

    Sets up a suffix filter on s3 bucket events.

        | *Required*: False
        | *Example*: ``"jpg"``

``sns`` Trigger *Keys*
======================

A Lambda trigger on SNS topic events.

``topic``
^^^^^^^^^

    The SNS topic name to monitor for events.

        | *Type*: string
        | *Required*: True

``sqs`` Trigger *Keys*
======================

A Lambda trigger on SQS queue events.

``queue_arn``
^^^^^^^^^^^^^

    SQS Queue ARN to use for triggering lambda.

        | *Type*: string
        | *Required*: True
        | *Example*: ``"arn:aws:sqs:us-east-1:111111111111:sqstest-queue"``

``batch_size``
^^^^^^^^^^^^^^

    The maximum number of items to retrieve in a single batch.

        | *Type*: int
        | *Required*: False
        | *Default*: ``10``
        | *Max*: ``10``