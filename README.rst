Spinnaker Foremast
==================

Foremast is a Spinnaker pipeline and infrastructure configuration and templating tool. 
Just create a couple JSON configuration files and then manually creating Spinnaker pipelines becomes a thing of the past.


Why Foremast?
-------------

- Do not want to create each Spinnaker pipeline manually in the UI.
- Pipelines should be versioned and easily reproducible.
- Provide a standardized pipeline for all apps but still allow for flexibility.

With Foremast, Developers create a couple simple JSON configs per application. 
These configs provide details on the pipeline and infrastructure specific to the application's needs. 
Foremast takes those configs, renders some Jinja2 templates, and then acts as a client for the 
Spinnaker Gate API. Foremast comes with generic templates for creating a simple pipeline but it can also 
point to external templates. This allows for custom pipelines to fit any workflow

Foremast Features
-----------------

- Dynamically generate Spinnaker pipelines based on JSON configs.
- Customizable pipelines through external Jinja2 Templates. See `Foremast templates`_ for examples.
- Dynamically generate AWS infrastructure based on pipeline configs.
- Set up resources not defined in Spinnaker, such as S3 buckets and IAM roles.
- Support for AWS Lambda pipelines.

Getting Started
---------------

Take a look at our `quick start guide`_ to for a quick introduction on how to use Foremast. 

Documentation
~~~~~~~~~~~~~

All the documentation can be viewed on `Read the Docs`_. You can find all configuration options, code information, 
and better examples there. 

Getting Help
~~~~~~~~~~~~~

For questions, support, or friendly conversation you can find us on Gitter_.

More Details
------------

Installing
~~~~~~~~~~

Installing the package will provide CLI commands for convenience.

.. code-block:: bash

    git clone https://github.com/gogoit/foremast.git
    cd foremast
    virtualenv -p python3 venv
    source venv/bin/activate
    pip install -U .

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

Entry Points
~~~~~~~~~~~~~

Foremast has a few easy to use CLI endpoints.

-  ``foremast-pipeline`` - Creates an application and pipeline Spinnaker
-  ``foremast-infrastructure`` - Sets up AWS infrastructure like s3, iam, elb,
   and security groups
-  ``foremast-pipeline-onetime`` - Generates a pipeline for deploying to one
   specific account
-  ``foremast-scaling-policy`` - Creates and attaches a scaling policy to an
   application server group.
-  ``foremast-pipeline-rebuild`` - rebuild pipelines after changes have been made

You can run any of these entries points from the command line. They rely on
environment variables and are ideal for running in a Jenkins job

.. code-block:: bash

    PROJECT=forrest GIT_REPO=core foremast-pipeline

Foremast Configuration
~~~~~~~~~~~~~~~~~~~~~~

A file at ``~/.foremast/foremast.cfg`` or ``/etc/foremast/foremast.cfg`` needs to exist in order to run foremast.

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

A :file:`pipeline_json`, will be needed for each application. We have a lot of
defaults in place for ``pipeline.json``, take a look at the :ref:`pipeline_json`
docs for all options.

*Minimum*

.. code-block:: json

    {
        "deployment": "spinnaker"
    }

*Example Deployment Environments Override*

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

application-master-{env}.json
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each deployment environment specified in the ``pipeline.json`` file will need an
accompanying ``application-master-{env}.json`` file in the same directory.

The \`application-master-{env} files have a lot of exposed values with sane
defaults. Please take a look at the :ref:`application_json` docs for all options.

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

.. _`Foremast templates`: https://github.com/gogoair/foremast-template-examples/
.. _`quick start guide`: https://example.com
.. _`Read the Docs`: http://example.com
.. _Gitter: http://example.com
