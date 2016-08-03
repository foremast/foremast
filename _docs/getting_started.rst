======================
Getting Started
======================

.. contents::
    :local:

This getting started guide will walk through the process of using Foremast to create an application in Spinnaker and dynamically generate a basic Spinnaker pipeline.


Getting started with Foremast consists of the following steps:

    1. Setting up configuration files
    2. Installing Foremast
    3. Setting up the variables
    4. Running Foremast


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

In ``~/runway`` creates a file ``pipeline.json`` with the contents::

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

Running Foremast
--------------------

After setting up all of the configs there are a couple of ways to run Foremast components. You can use our bundled CLI endpoints that look at environment variables, or you can call each individual component with appropriate arguments on the CLI

Both methods will generate the same out come. An application created in Spinnaker and a pipeline generated based on the configs.

Variables Needed
****************

For both methods you will want to set the following variables. Method 1 will look at the environoment for these, Method 2 you can just pass them directly as arguments.

    | ``TRIGGER_JOB``: The name of the Jenkins job that Spinnaker should look for as a trigger
    | ``APPNAME``: The full name of your application in Spinnaker. We recommend ``${GIT_REPO}${PROJECT}``
    | ``EMAIL``: email address associated with application in Spinnaker
    | ``PROJECT``: The namespace or group of the application being set up
    | ``GIT_REPO``: The name of the repo in the above namespace/group
    | ``RUNWAY_DIR``: Path to the pipeline.json and application-master-$account.json files created above


Method 1
*********

This is our recommended method and how we internally at Gogo run Foremast. You need to first set the environment variables from above. 

With the environment variables defined, you can simply run the command ``prepare-app-pipeline`` from the command line. This will create the Application in Spinnaker as well as generate a base pipeline.

Method 2
********

This method is more explicit and requires calling multiple Foremast components to create the configs, create the application, and generate the pipeline::

    create-configs -o ./raw.properties -g ${PROJECT}/${GIT_REPO} -r ${RUNWAY_DIR}

    create-app -a ${APPNAME} --email ${EMAIL} --project ${PROJECT} --repo ${GIT_REPO}

    create-pipeline -a ${APPNAME} --triggerjob ${TRIGGER_JOB}



Continuing with Foremast
------------------------

This is only the tip of what Foremast can do. It also has functionality for creating scaling policies, setting up AWS infrastructure (elbs, security groups, iam policies, s3 buckets), sending slack notifications, and destorying old infrastructure. Take a look at our internal workflow docs for more detail on how Foremast is used at Gogo.







