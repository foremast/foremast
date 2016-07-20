Spinnaker Foremast
==================

This project contains different modules for managing applications, pipelines,
and AWS infrastructure through Spinnaker

Basic Task Overview
-------------------

These are designed to be loosely coupled applications and we will continue to
update this README as the project grows.

Usage
-----

Run Jobs
~~~~~~~~

Commands can be run in the same way that Jenkins will execute using the below
entry points.

Entry Points
^^^^^^^^^^^^

-  ``prepare-app-pipeline`` - Creates an application and pipeline Spinnaker
-  ``prepare-infrastructure`` - Sets up AWS infrastructure like s3, iam, elb,
   and security groups
-  ``prepare-onetime-pipeline`` - Generates a pipeline for deploying to one
   specific account
-  ``create-scaling-policy`` - Creates and attaches a scaling policy to an
   application server group.
-  ``rebuild_pipelines`` - rebuild pipelines after changes have been made
-  ``slack-notify`` - sends a slack notification to the proper channels

You can run any of these entries points from the command line. They rely on
environment variables and are ideal for running in a Jenkins job

.. code-block:: bash

    PROJECT=forrest GIT_REPO=core EMAIL=test@example.com prepare-app-pipeline

Individual Packages
~~~~~~~~~~~~~~~~~~~

Run code directly without installing the ``foremast`` package.

.. code-block:: bash

    virtualenv venv
    source ./venv/bin/activate
    pip install -U -r requirements.txt

    python -m src.foremast.app -h
    python -m src.foremast.configs -h
    python -m src.foremast.configurations -h
    python -m src.foremast.dns -h
    python -m src.foremast.elb -h
    python -m src.foremast.iam -h
    python -m src.foremast.pipeline -h
    python -m src.foremast.s3 -h
    python -m src.foremast.securitygroup -h

Install
~~~~~~~

Installing the package will provide CLI commands for convenience.

.. code-block:: bash

    virutalenv venv
    source ./venv/bin/activate
    pip install .

    create-app -h
    create-configs -h
    create-dns -h
    create-elb -h
    create-iam -h
    create-pipeline -h
    create-s3 -h
    create-sg -h

Testing
~~~~~~~

Run any unit tests available in ``./tests/``.

.. code-block:: bash

    virtualenv venv
    source ./venv/bin/activate
    pip install -U -r requirements-dev.txt

    tox
    # OR
    ./runtests.py

Implementation
--------------

See ``pipes-pipeline-prepare`` in `dsl.groovy <runway/dsl.groovy>`_ for Jenkins
Job configuration.

#. Create logical Spinnaker app (triggered by Git Hook)
#. Call downstream Job to manage infrastructure
#. Read configurations from ``application-master-{env}.json`` and
   ``pipeline.json``
#. Generates an application and a pipeline in Spinnaker
#. An infrastructure stage is created in the pipeline which does the following
   when ran:

   #. Create/modify IAM Profile and Role
   #. Create/skip S3 Archaius application.properties file
   #. Create/modify Security Groups
   #. Create/modify ELB
   #. Create DNS record to ELB
   #. Create/modify application pipeline

Not Used
~~~~~~~~

-  Create/modify server group/ASG

   -  This is part of Spinnaker "deploy" stages and is handled completely by
      Spinnaker

Technology Used
---------------

See `requirements <requirements.txt>`_ for package listing.

#. Python3
#. Jinja2 templating
#. Python Requests
#. Argparse for arguments
#. Boto3 (direct AWS access to parts not exposed by Spinnaker, e.g. S3)

Runway Configuration Files
--------------------------

To begin using Foremast, you must have a few JSON configuration files defined
for each application

pipeline.json
~~~~~~~~~~~~~

``pipeline.json``, will be needed in some direct of your application. We use the
``runway`` directory. We have a lot of defaults in place for ``pipeline.json``,
take a look at the docs for all options.

Minimum
^^^^^^^

.. code-block:: json

    {
        "deployment": "spinnaker"
    }

Example Deployment Environments Override
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Custom deployment environment order and selection can be provided in the ``env``
key. When missing, the default provided is ``{"env": ["stage", "prod"]}``. Here,
the order matters and Pipeline will be generated in the given order.

.. code-block:: json

    {
        "deployment": "spinnaker",
        "env": [
            "prod"
        ]
    }

Complete JSON Override
^^^^^^^^^^^^^^^^^^^^^^

Complete manual overrides can also be provided based on JSON configuration for a
Spinnaker Pipeline, but are not supported. JSON dump can be found in the
Pipeline view.

.. code:: json

    {
        "deployment": "spinnaker",
        "env": [
            "prod"
        ],
        "prod": {
            "_Custom Spinnaker Pipeline configuration": "Insert here."
        }
    }

application-master-{env}.json
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each deployment environment specified in the ``pipeline.json`` file will need an
accompanying ``application-master-{env}.json`` file in the same directory.

The \`application-master-{env} files have a lot of exposed values with sane
defaults. Please take a look at the docs for all options.

application-master-{env}.json example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: json

    {
      "security_group": {
        "description": "something useful",
        "elb_extras": ["sg_offices"],
        "ingress": {
        },
        "egress": "0.0.0.0/0"
      },
      "app": {
        "instance_type": "t2.small",
        "app_description": "Edge Forrest Demo application",
        "instance_profile": "forrest_edge_profile"
      },
      "elb": {
        "subnet_purpose": "internal",
        "target": "TCP:8080",
        "ports": [
          {"loadbalancer": "HTTP:80", "instance": "HTTP:8080"}
        ]
      },
      "asg": {
        "subnet_purpose": "internal",
        "min_inst": 1,
        "max_inst": 1,
        "scaling_policy": {
            "metric": "CPUUtilization",
            "threshold": 90,
            "period_minutes": 10,
            "statistic": "Average"
            }
      },
      "regions": ["us-east-1"],
      "dns" : {
        "ttl": 120
        }
    }

TODOs
-----

-  [] Abstract Gogoutils or make public
-  [] Make prop\_path implied, or handle it better
-  [] Open Source!
-  [] Add github support
