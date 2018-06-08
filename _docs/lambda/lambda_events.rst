.. _lambda_events:

==========================
Lambda Triggers and Events
==========================

.. contents::
   :local:

Purpose
-------

Foremast supports multiple Lambda events. These are configured in the :ref:`application_json` config and set as a list under the :ref:`lambda_trigger` key.

Example Configuration
---------------------

This example would go in the :ref:`application_json` configuration file.

.. code-block:: json

   {
     "lambda_triggers": [
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
         "type": "cloudwatch-event",
         "schedule": "rate(5 minutes)",
         "rule_name": "app cron - 5min",
         "rule_description": "triggers lambda function every five minutes"
       },
       {
         "type": "cloudwatch-logs",
         "log_group": "/aws/lambda/awslimit_test",
         "filter_name": "Trigger lambda on every WARNING message",
         "filter_pattern": ""
       },
       {
         "type": "api-gateway",
         "api_name": "lambdatest-api",
         "resource": "/index",
         "method": "GET"
       }
     ]
   }

Configuration Details
----------------------

``type``
~~~~~~~~

Specifies what type of Lambda event/trigger to use. This needs to be set for all events.

    | *Options*:

        - ``"api-gateway"`` - API Gateway Lambda trigger
        - ``"cloudwatch-event"`` - Cloudwatch event Lambda trigger
        - ``"cloudwatch-logs"`` - Cloudwatch logs event Lambda trigger
        - ``"dynamodb-streams"`` - DynamoDB event Lambda trigger
        - ``"s3"`` - S3 Lambda trigger
        - ``"sns"`` - SNS Lambda trigger

    | *Required*: True

S3 Event
~~~~~~~~

A Lambda trigger on S3 bucket actions.

``bucket``
**********

The bucket of the event to monitor.

    | *Required*: True


``events``
**********

The S3 event to trigger the lambda function from.

    | *Type*: List
    | *Required*: True
    | *Example*: ``["s3:ObjectCreated:*", "s3:ObjectedRemoved:Delete"]``

``prefix``
**********

Sets up a prefix filter on S3 bucket events.

    | *Required*: False
    | *Example*: ``"logs/"``

``suffix``
**********

Sets up a suffix filter on s3 bucket events.

    | *Required*: False
    | *Example*: ``"jpg"``

SNS Event
~~~~~~~~~

A Lambda trigger on SNS topic events.

``topic``
*********

The SNS topic name to monitor for events.

    | *Required*: True

Cloudwatch Event
~~~~~~~~~~~~~~~~

A Cloudwatch Scheduled event for Lambda triggers.

``schedule``
************

The rate or cron string to trigger the Lambda function.

    | *Required*: True
    | *Examples*:

        - ``"rate(5 minutes)"``
        - ``"cron(0 17 ? * MON-FRI *)"``

``rule_name``
*************

The name of the cloudwatch rule being created.

    | *Required*: False
    | *Default*: ``"{app_name}+{schedule}"``

``rule_description``
*********************

Description of the rule being created.

    | *Required*: False

Cloudwatch Log Event
~~~~~~~~~~~~~~~~~~~~

A lambda event that triggers off a Cloudwatch log action.

``log_group``
*************

The name of the log group to monitor.

    | *Required*: True
    | *Example*: ``"/aws/lambda/test_function"``

``filter_name``
***************

The name of the filter on log event.

    | *Required*: True

``filter_pattern``
******************

The pattern to look for in the ``log_group`` for triggering a Lambda function.

    | *Required*: True
    | *Example*: ``"warning"``

API Gateway Event
~~~~~~~~~~~~~~~~~

Sets up an API Gatway event to trigger a lambda function.

``api_name``
************

The name of an existing API Gateway. If not provided, an API will be created.

    | *Required*: False
    | *Default*: ``{app_name}``

``resource``
************

The API resource to tie the Lambda function to.

    | *Required*: True
    | *Example*: ``"/test"``

``method``
***********

The API Method to trigger the Lambda function.

    | *Required*: True
    | *Example*: ``"GET"``

DynamoDB Streams
~~~~~~~~~~~~~~~~

A lambda event that triggers off a DynamoDB Stream. Make sure to grant access
to the DynamoDB table for the lambda iam role via the services block by 
providing the table name. If both stream and table key present, default behavior uses stream.

``stream``
*********

DynamoDB Stream ARN to use for triggering lambda. Only table or stream needed, not both.

    | *Required*: False
    | *Example*: ``"arn:aws:dynamodb:us-east-1:111111111111:table/foremast-test/stream/2018-06-07T03:12:22.234"``

``table``
***************

DynamoDB Table ARN to use for triggering lambda. Only table or stream needed, not both.

    | *Required*: False
    | *Example*: ``"arn:aws:dynamodb:us-east-1:111111111111:table/foremast-test"``
