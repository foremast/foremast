Lambda Pipeline
===============

.. contents::
   :local:

Overview
--------

Foremast supports the ability to setup Lambda infrastucture and build a pipeline around Lambda deployments. This was designed to be very similar to the default EC2 pipeline. It requires the same configuration files and general setup.

Lambda Specific Setup
---------------------

#. Look at the :ref:`getting_started` guide for basic setup. The Lambda process will be very similar
#. Look at the :ref:`lambda_block` configurations in :ref:`pipeline_json` and :ref:`application_json`.
#. In :ref:`pipeline_json` set ``"type" : "lambda"`` in order for Foremast to treat the application as a Lambda function.
#. Setup the desired Lambda triggers. See :ref:`lambda_events` for details.

Lambda Pipeline Example
-----------------------

#. Generate a ZIP artifact of your desired Lambda function
#. Trigger Spinnaker Lambda pipeline
#. Spinnaker runs "Infrastructure Setup Lambda"

    #. Sets up default function
    #. Sets up event triggers
    #. Sets up IAM Roles
    #. Sets up security groups

#. Spinnaker runs a "Deploy Lambda" stage

    #. This stage uploads the ZIP artifact to the created Lambda function

#. Manual Judgement checkpoint for deploying to the next environment
#. Repeat steps 3-5 for each desired environment

.. image:: /_static/lambda_example.png
