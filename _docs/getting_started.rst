======================
Getting Started
======================

.. contents::
    :local:

Getting started with Foremast consists of the following steps:

    1. Setting up configuration files
    2. Installing Foremast
    3. Setting environment variables
    4. Running desired Foremast endpoint


Configuration Setup
-------------------

There are a few :doc:`configuration_files` that will need to be setup before Foremast can be used

    1. :doc:`foremast_config` - This config holds basic info such Spinnaker URL, tokens, and environments
    2. :doc:`aws_creds` - This is the Boto3 credentials file for AWS access
    3. :doc:`pipeline_json` - Pipeline configuration. Discussed in more detail below
    4. :doc:`application_json` - Application AWS configuration. Discussed in more detail below

Pipeline Configs
*******************

The :doc:`pipeline_json` and :doc:`application_json` are critical files that determine on how an application pipeline will work. Theses configurations need to exist for each application that you plan on using Foremast to deploy. We recommend keeping these files in the same repository as your application but as long as they are on the same local machine as the Foremast runner they can be used.

In ``~/runway`` creates a file ``pipeline.json`` with the contents ::

    {
        "deployment": "spinnaker",
        "env": [ "account1", "accounts2"]
    }

In the same ``~/runway`` directory, create a file ``application-master-$account.json`` where ``$accounts`` is the same name as an account in your AWS credentials file and in your ``env`` list in pipeline.json.
This file can be empty and it will just use the defaults defined at :doc:`application_json`. It is sugguested that you look through the docs and decide what values to set.

**Note:** You will need an ``application-master-$account.json`` config for each ``$account`` that you are deploying to.

See :doc:`pipeline_json` and :doc:`application_json` for all configuration options


Install Foremast
-----------------

In order to use Foremast, you will need to install it in a Python environment. Below is our prefered method::

    virtualenv -p python3 venv
    . venv/bin/activate
    pip install -U .

Once Foremast is installed, you will have access to all of the endpoints in the CLI


Environment Variables
---------------------


Creating a Pipeline
--------------------






