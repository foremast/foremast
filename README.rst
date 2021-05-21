Spinnaker Foremast
==================


.. image:: https://github.com/foremast/foremast/actions/workflows/githubactions-tox.yml/badge.svg
    :target: https://github.com/foremast/foremast/actions/workflows/githubactions-tox.yml

.. image:: https://github.com/foremast/foremast/actions/workflows/codeql-analysis.yml/badge.svg
    :target: https://github.com/foremast/foremast/actions/workflows/codeql-analysis.yml

.. image:: https://badges.gitter.im/foremast/foremast.svg
   :alt: Join the chat at https://gitter.im/foremast/foremast
   :target: https://gitter.im/foremast/foremast?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

.. image:: https://badge.fury.io/py/foremast.svg
    :target: https://badge.fury.io/py/foremast

Foremast is a Spinnaker pipeline and infrastructure configuration and
templating tool.  Just create a couple JSON configuration files and then
manually creating Spinnaker pipelines becomes a thing of the past.

.. image:: https://s3.amazonaws.com/gogo-oss-logos/Foremast/Foremast+Logo-text-300.png
   :align: center


Why Foremast?
-------------

- No manual creation of pipelines in the Spinnaker UI
- Reproducible and versioned Spinnaker pipelines
- Standardized pipelines with flexibilty for application specific needs

With Foremast, Developers create a couple simple JSON configs per application.
These configs provide details on the pipeline and infrastructure specific to
the application's needs.  Foremast takes those configs, renders some Jinja2
templates, and then acts as a client for the Spinnaker Gate API. Foremast comes
with generic templates for creating a simple pipeline but it can also point to
external templates for custom pipelines that fit any workflow.

Foremast Features
-----------------

- Dynamically generate Spinnaker pipelines based on JSON configs
- Customizable pipelines through external Jinja2 Templates, see `Foremast templates`_ for examples
- Dynamically generate AWS infrastructure based on pipeline configs
- Set up resources not defined in Spinnaker, such as S3 buckets and IAM roles
- Support for AWS Lambda pipelines

Getting Started
---------------

Take a look at `quick start guide`_ for a quick introduction on how to use
Foremast.

We also have a blog post to help you get started: `Automate Spinnaker Pipeline Creation`_

Documentation
~~~~~~~~~~~~~

All the documentation can be viewed on `Read the Docs`_. You can find all
configuration options, code information, and better examples there.

Development
~~~~~~~~~~~

See the `contribution guide`_ for information on code style, contributing, and
testing.

Getting Help
~~~~~~~~~~~~~

For questions, support, or friendly conversation you can find us on `Gitter`_.

More Details
------------

Installing
~~~~~~~~~~

Installing the package will provide CLI commands for convenience.

.. code-block:: bash

   virtualenv -p python3 venv
   source venv/bin/activate
   pip install foremast

Entry Points
~~~~~~~~~~~~~

Foremast has a few easy to use CLI endpoints.

- ``foremast-pipeline`` - Creates an application and pipeline Spinnaker
- ``foremast-infrastructure`` - Sets up AWS infrastructure like s3, iam, elb,
  and security groups
- ``foremast-pipeline-onetime`` - Generates a pipeline for deploying to one
  specific account
- ``foremast-scaling-policy`` - Creates and attaches a scaling policy to an
  application server group.
- ``foremast-pipeline-rebuild`` - rebuild pipelines after changes have been
  made

You can run any of these entries points from the command line. They rely on
environment variables and are ideal for running in a Jenkins job

.. code-block:: bash

    PROJECT=forrest GIT_REPO=core RUNWAY_DIR=path/to/pipeline_configs foremast-pipeline

Foremast Configuration
~~~~~~~~~~~~~~~~~~~~~~

A file at ``{pwd}/.foremast/foremast.cfg``, ``~/.foremast/foremast.cfg``, or
``/etc/foremast/foremast.cfg`` needs to exist in order to run foremast.

.. code-block:: bash

    [base]
    domain = example.com
    envs = dev,stage,prod
    regions = us-east-1
    gate_api_url = http://gate.example.com:8084

Runway Configuration Files
~~~~~~~~~~~~~~~~~~~~~~~~~~

To begin using Foremast, you must have a few JSON configuration files defined
for each application

pipeline.json
^^^^^^^^^^^^^

This file will be needed for each application. Foremast has a lot of defaults
in place for ``pipeline.json``, take a look at the `pipeline.json`_ docs for
all options.

*Minimum*

.. code-block:: json

    {
        "deployment": "spinnaker"
    }

*Example Deployment Environments Override*

Custom deployment environment order and selection can be provided in the
``env`` key. When missing, the default provided is ``{"env": ["stage",
"prod"]}``. Here, the order matters and Pipeline will be generated in the given
order.

.. code-block:: json

    {
        "deployment": "spinnaker",
        "env": [
            "prod"
        ]
    }

application-master-{env}.json
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each deployment environment specified in the ``pipeline.json`` file will need
an accompanying ``application-master-{env}.json`` file in the same directory.

The \`application-master-{env} files have a lot of exposed values with sane
defaults. Please take a look at the `application.json`_ docs for all options.

*application-master-{env}.json example*

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

.. _`Foremast templates`: https://github.com/foremast/foremast-template-examples/
.. _`quick start guide`: http://foremast.readthedocs.io/en/latest/getting_started.html#quick-start-guide
.. _`automate spinnaker pipeline creation`: https://tech.gogoair.com/foremast-automate-spinnaker-pipeline-creation-2b2aa7b2c5e4#.qplfw19cg
.. _`Read the Docs`: http://foremast.readthedocs.io/en/latest/
.. _`contribution guide`: http://foremast.readthedocs.io/en/latest/CONTRIBUTING.html
.. _`Gitter`: https://gitter.im/foremast/foremast
.. _`pipeline.json`: http://foremast.readthedocs.io/en/latest/configuration_files/pipeline_json/index.html
.. _`application.json`: http://foremast.readthedocs.io/en/latest/configuration_files/application_json.html
