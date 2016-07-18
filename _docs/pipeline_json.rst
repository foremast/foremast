=============
pipeline.json
=============

.. contents::

Purpose
-------
This configuration file is used for defining pipeline settings that affect the pipeline as a whole, not a specific account/environment.

Example Configuration
---------------------

.. literalinclude:: ../src/foremast/templates/pipeline.json.j2

Configuration Details
----------------------

``owner_email``
~~~~~~~~~~~~~~~

The application owners email address. This is not used directly in the pipeline but can be consumed by other tools

    | *Default*: ``null``

``documentation``
~~~~~~~~~~~~~~~~~

Link to the applications documentation. This is not used directly in the pipeline but can be consumed by other tools

    | *Default*: ``null``

``notifications`` Block
~~~~~~~~~~~~~~~~~~~~~~~

Where to send pipeline failure notifications

``email``
**********

Email address to send pipeline failures (email must be configured in Spinnaker Echo)

    | *Default*: ``null``

``slack``
**********

Slack channel to send pipeline failures (Slack must be configured in Spinnaker Echo)

    | *Default*: ``null``

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

The base AMI to use for baking the application

    | *Default*: ``"tomcat8"``

``envs``
~~~~~~~~

List of accounts that the application will be deployed to. Order matters as it defines the order of the pipeline. The accounts should be named the same as you have them in Spinnaker Clouddriver

    | *Type*: List of strings
    | *Default*: ``["stage", "prod"]``

``image`` Block
~~~~~~~~~~~~~~~

Holds settings for the baked image

``root_volume_size``
********************

Defines the root volume size of the resulting AMI in GB

    | *Type*: int
    | *Units*: Gigabyte
    | *Default*: `6`
