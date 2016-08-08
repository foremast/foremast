================================
foremast.cfg
================================

.. contents::
   :local:

Purpose
-------
This configuration holds information necessary for running foremast such as auth tokens, URLs, whitelists etc

Example Configuration
----------------------

.. literalinclude:: ../src/foremast/templates/configs/foremast.cfg.example

Configuration Locations
------------------------
Foremast will look in the following locations, in order, for the foremast.cfg config file.

1. ``./.foremast/foremast.cfg``
2. ``~/.foremast/.foremast.cfg``
3. ``/etc/foremast/foremast/cfg``

Configuration Details
----------------------

``[base]``
~~~~~~~~~~~~~

Sections for base information such as urls and general configurations

``domain``
***********

The base domain of your applications. Used for generating DNS

    | *Required*: Yes

``envs``
*********

Comma delimiated list of environments/applications that will be managed with Foremast

    | *Example*: ``dev,stage,prod``
    | *Required*: Yes

``regions``
***********

Comma delimiated list of AWS regions managed by Foremast

    | *Example*: ``us-east-1,us-west-2``
    | *Required*: Yes

``ami_json_url``
*****************

FQDN of where to query for AMI ID look ups. See :doc:`ami_json` for more details

    | *Required*: No


``gitlab_url``
***************

FQDN of gitlab. Will be used for handling API calls to Gitlab

    | *Required*: No

``gate_api_url``
*****************

FQDN Of your spinnaker Gate instance. This is where all API calls to Spinnaker will go

    | *Required*: Yes

``templates_path``
******************

Path to custome templates directory. If provided, Foremast will first look in this directory for any templates. This can be an absolute path, or a path relative to where you where you are running the Foremast commands. See :doc:`pipeline_examples` for more details on custom templates.

    | *Required*: No

``default_securitygroups``
**************************
Comma seperated list of security groups to include for all deployments

    | *Required*: No
    | *Example*: ``office,test_sg,example``

``[credentials]``
~~~~~~~~~~~~~~~~~

Section for handling credential configurations such as tokens, usernames, and passwords

``gitlab_token``
****************

Gitlab token used for authentication in Foremast

    | *Required*: No

``slack_token``
****************

Slack token used for authentication when sending Slack messages from Foremast

    | *Required*: No


``[whitelists]``
~~~~~~~~~~~~~~~~~

Sections for configuring whitelist info

``asg_whitelist``
*****************

Comma delimiated list of applications to whitelist from ASG rules

    | *Required*: No
