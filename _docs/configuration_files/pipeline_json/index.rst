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
----------------------


``type``
~~~~~~~~

Specifies what type of pipeline to use for the application.

    | *Default*: ``"ec2"``
    | *Options*:

        - ``"lambda"`` - Sets up the AWS Lambda pipeline and infrastructure
        - ``"ec2"`` - Sets up the AWS EC2 pipeline and infrastructure

``owner_email``
~~~~~~~~~~~~~~~

The application owners email address. This is not used directly in the pipeline but can be consumed by other tools

    | *Default*: ``null``

``documentation``
~~~~~~~~~~~~~~~~~

Link to the applications documentation. This is not used directly in the pipeline but can be consumed by other tools

    | *Default*: ``null``

.. include:: notifications.rest

``promote_restrict``
~~~~~~~~~~~~~~~~~~~~

Restriction setting for promotions to prod* accounts.

    | *Default*: ``"none"``
    | *Options*:

       - ``"masters-only"`` - only masters/owners on a repository can approve deployments
       - ``"members-only"`` - Any member of a repository can approve deployments
       - ``"none"`` - No restrictions

``base``
~~~~~~~~

The base AMI to use for baking the application. This can be an alias defined in :ref:`ami-lookup.json` or an AMI Id.

    | *Default*: ``"tomcat8"``

``envs``
~~~~~~~~

List of accounts that the application will be deployed to. Order matters as it defines the order of the pipeline. The accounts should be named the same as you have them in Spinnaker Clouddriver

    | *Type*: List of strings
    | *Default*: ``["stage", "prod"]``

.. include:: image.rest
.. include:: lambda.rest
.. include:: services.rest
