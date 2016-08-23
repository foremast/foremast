=============
Lambda Events
=============

.. contents::
   :local:

Purpose
-------
Foremast supports multiple Lambda events. These are configured in the :doc:`application_json` config and set as a list under the ``lambda_triggers`` key.

Example Configuration
---------------------

This example would go in the :doc:`application_json` configuration file

::

      "lambda_triggers": [
        {
          "type": "s3",
          "bucket": "app-bucket-dev",
          "events": ["s3:ObjectCreated:*"],
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
          "method": "GET",
        }
      ]
      }


Configuration Details
----------------------

``type``
~~~~~~~~

Specifies what type of Lambda event/trigger to use. This needs to be set for all events

    | *Options*:

        - ``"s3"`` - S3 Lambda trigger
        - ``"sns"`` - SNS Lambda trigger
        - ``"cloudwatch-event"`` - Cloudwatch event Lambda trigger
        - ``"cloudwatch-logs"`` - Cloudwatch logs event Lambda trigger
        - ``"api-gateway"`` - API Gateway Lambda trigger
    | *Required*: True

S3 Event
~~~~~~~~

``bucket``
**********

``events``
**********

``prefix``
**********

``suffix``
**********

SNS Event
~~~~~~~~~

``topic``
*********

Cloudwatch Event
~~~~~~~~~~~~~~~~

``schedule``
************

``rule_name``
*************

``rule_description``
*********************

Cloudwatch Log Event
~~~~~~~~~~~~~~~~~~~~

``log_group``
*************

``filter_name``
***************

``filter_pattern``
******************

API Gateway Event
~~~~~~~~~~~~~~~~~

``api_name``
************

``resource``
************

``method``
***********
