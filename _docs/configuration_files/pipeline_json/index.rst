.. _pipeline_json:

=============
pipeline.json
=============

.. contents::
   :local:

Purpose
-------

This configuration file is used for defining pipeline settings that affect the pipeline as a whole, not a specific account/environment.

Example Configuration
---------------------

.. literalinclude:: ../../../src/foremast/templates/configs/pipeline.json.j2

Configuration Details
---------------------

.. _pipeline_type:

``type``
~~~~~~~~

Specifies what type of pipeline to use for the application.

    | *Type*: string
    | *Default*: ``"ec2"``
    | *Options*:

        - ``"ec2"`` - Sets up an AWS EC2 pipeline and infrastructure
        - ``"datapipeline"`` - Sets up an AWS Data Pipeline infrastructure
        - ``"lambda"`` - Sets up an AWS Lambda pipeline and infrastructure
        - ``"stepfunction"`` - Sets up an AWS Step Function pipeline and infrastructure
        - ``"cloudfunction"`` - Sets up a GCP Cloud Function pipeline, infrastructure and deploys code
        - ``"s3"`` - Sets up an AWS S3 pipeline and infrastructure
        - ``"rolling"`` - Sets up a "rolling" style pipeline. Requires custom templates.
        - ``"manual"`` - Sets up pipelines from raw Spinnaker Pipeline JSON; more info: :doc:`../advanced_usages/index`.

``owner_email``
~~~~~~~~~~~~~~~

The application owners email address. This is not used directly in the pipeline but can be consumed by other tools

    | *Type*: string
    | *Default*: ``null``

``documentation``
~~~~~~~~~~~~~~~~~

Link to the applications documentation. This is not used directly in the pipeline but can be consumed by other tools

    | *Type*: string
    | *Default*: ``null``

.. include:: notifications.rest
.. include:: pipeline_notifications.rest

``promote_restrict``
~~~~~~~~~~~~~~~~~~~~

Restriction setting for promotions to prod* accounts.

    | *Type*: string
    | *Default*: ``"none"``
    | *Options*:

       - ``"masters-only"`` - only masters/owners on a repository can approve deployments
       - ``"members-only"`` - Any member of a repository can approve deployments
       - ``"none"`` - No restrictions

``base``
~~~~~~~~

The base AMI to use for baking the application. This can be an alias defined in :ref:`ami-lookup.json` or an AMI Id.

    | *Type*: string
    | *Default*: ``"tomcat8"``

``env``
~~~~~~~

List of accounts that the application will be deployed to. Order matters as it defines the order of the pipeline. The accounts should be named the same as you have them in Spinnaker Clouddriver

    | *Type*: array
    | *Default*: ``["stage", "prod"]``

.. include:: image.rest
.. include:: lambda.rest
.. include:: services.rest
.. include:: chaos_monkey.rest
.. include:: instance_links.rest
.. include:: permissions.rest
.. include:: traffic_guards.rest
.. include:: cloudfunction.rest
