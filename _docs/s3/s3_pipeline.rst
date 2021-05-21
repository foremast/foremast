S3 Pipeline
===============

.. contents::
   :local:

Overview
--------

Foremast supports the ability to setup S3 infrastucture and build a pipeline around S3 deployments. This was designed to be very similar to the default EC2 pipeline. It requires the same configuration files and general setup.

S3 Specific Setup
-----------------

#. Look at the :ref:`getting_started` guide for basic setup. The S3 process will be very similar
#. Look at the :ref:`s3_block` configurations in :ref:`pipeline_json` and :ref:`application_json`.
#. In :ref:`pipeline_json` set ``"type" : "s3"`` in order for Foremast to treat the application as an S3 deployment.

S3 Pipeline Example
-------------------

#. Prepare a local folder containing your desired S3 deployment (commonly an uncompressed tar.gz)
#. Trigger Spinnaker S3 pipeline
#. Spinnaker runs "Infrastructure Setup S3"

    #. Sets up S3 bucket
    #. Attaches S3 bucket policies and metadata
    #. Creates friendly DNS record for s3 bucket if website enabled

#. Spinnaker runs a "Deploy S3" stage

    #. This stage uploads the local folder containing your artifacts to the created S3 bucket

#. Manual Judgement checkpoint for deploying to the next environment
#. Repeat steps 3-5 for each desired environment

.. image:: /_static/s3_example.png