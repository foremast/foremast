.. _advance_usages:

======================
Advance Usages
======================

.. contents::
    :local:

This section will show many advance usages of Foremast.

Environment Variables
---------------------

These are environment variables used when executing Foremast

    | ``TRIGGER_JOB``: The name of the Jenkins job that Spinnaker should look for as a trigger
    | ``APPNAME``: The full name of your application in Spinnaker. ``${GIT_REPO}${PROJECT}`` is default
    | ``EMAIL``: Email address associated with application in Spinnaker
    | ``PROJECT``: The namespace or group of the application being set up
    | ``GIT_REPO``: The name of the repo in the above namespace/group
    | ``RUNWAY_DIR``: Path to the ``pipeline.json`` and ``application-master-$account.json`` files created above

Pipeline Configs
----------------

The :ref:`pipeline_json` and :ref:`application_json` are critical files that determine on how each application in the pipeline will work. We recommend keeping these files in the same repository as your application but as long as they are on the same local machine as the Foremast runner they can be used.

In ``~/runway`` create a file ``pipeline.json`` with the contents::

    {
        "deployment": "spinnaker",
        "env": [ "account1", "account2"]
    }

In the same ``~/runway`` directory, create a file ``application-master-$account.json`` where ``$account`` is the same name as an account in your AWS credentials file and in your ``env`` list in pipeline.json.
This file can be empty and it will just use the defaults provided at :ref:`application_json`.

**Note:** You will need an ``application-master-$account.json`` config for each ``$account`` that you are deploying to.

See :ref:`pipeline_json` and :ref:`application_json` for all configuration options.

Running Foremast
----------------

After setting up all of the configs there are a couple of ways to run Foremast components. You can use our bundled CLI endpoints that look at environment variables, or you can call each individual component with appropriate arguments on the CLI

Both methods will generate the same outcome. An application created in Spinnaker and a pipeline generated based on the configs.


Method 1
********

This is our recommended method and how we internally at Gogo run Foremast. You need to first set the environment variables from above.

With the environment variables defined, you can simply run the command ``foremast-pipeline`` from the command line. This will create the Application in Spinnaker as well as generate a base pipeline.

Method 2
********

This method is more explicit and requires calling multiple Foremast components to create the configs, create the application, and generate the pipeline::

    create-configs -o ./raw.properties -g ${PROJECT}/${GIT_REPO} -r ${RUNWAY_DIR}

    create-app -a ${APPNAME} --email ${EMAIL} --project ${PROJECT} --repo ${GIT_REPO}

    create-pipeline -a ${APPNAME} --triggerjob ${TRIGGER_JOB}

Next Steps
----------
Take a look at the :doc:`infra_assumptions` docs for details on the necessary Jenkins jobs.

This is only the tip of what Foremast can do. It also has functionality for creating scaling policies, setting up AWS infrastructure (elbs, security groups, iam policies, s3 buckets), sending slack notifications, and destroying old infrastructure. Take a look at our internal workflow docs for more detail on how Foremast is used at Gogo.
