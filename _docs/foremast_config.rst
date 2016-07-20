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

.. literalinclude:: .foremast/foremast.cfg

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
