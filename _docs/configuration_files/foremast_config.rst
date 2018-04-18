.. _foremast_config:

========================
foremast.cfg / config.py
========================

.. contents::
   :local:

Purpose
-------

This configuration holds information necessary for running foremast such as auth
tokens, URLs, whitelists etc

Example Configuration
---------------------

.. literalinclude:: ../../src/foremast/templates/configs/foremast.cfg.example
.. literalinclude:: ../../src/foremast/templates/configs/config.py.example

Configuration Locations
-----------------------

Foremast will look in the following locations, in order, for the
``foremast.cfg`` or ``config.py`` config file.

1. ``./.foremast/foremast.cfg``
2. ``~/.foremast/.foremast.cfg``
3. ``/etc/foremast/foremast/cfg``
4. ``./config.py``

Configuration Details
---------------------

``[base]``
~~~~~~~~~~

Sections for base information such as urls and general configurations

``domain``
**********

The base domain of your applications. Used for generating DNS

    | *Required*: Yes

``envs``
********

Comma delimited list of environments/applications that will be managed with
Foremast

    | *Example*: ``dev,stage,prod``
    | *Required*: Yes

``types``
*********

List of foremast managed Pipeline types to allow.

    | *Type*: str
    | *Example*: ``ec2,lambda,manual``
    | *Default*: ``ec2,lambda``
    | *Required*: No

``regions``
***********

Comma delimiated list of AWS regions managed by Foremast

    | *Example*: ``us-east-1,us-west-2``
    | *Required*: Yes

``ami_json_url``
****************

FQDN of where to query for AMI ID look ups. See :doc:`ami_json` for more details

    | *Required*: No


``gitlab_url``
**************

FQDN of gitlab. Will be used for handling API calls to Gitlab

    | *Required*: No

``gate_api_url``
****************

FQDN Of your spinnaker Gate instance. This is where all API calls to Spinnaker
will go

    | *Required*: Yes

.. _templates_path:

``templates_path``
******************

Path to custom templates directory. If provided, Foremast will first look in
this directory for any templates. This can be an absolute path, or a path
relative to where you where you are running the Foremast commands. See
:ref:`pipeline_examples` for more details on custom templates.

    | *Required*: No

``default_ec2_securitygroups``
******************************

Comma separated list or json of EC2 security groups to include for all
deployments. If a comma separated list is given, the groups are applied to all
environments. If a json is provide, it assigns groups only to the specified
environment.

    | *Required*: No
    | *Example*: ``office,test_sg,example``
    | *Example (json)*: ``{"dev": ["sg1", "sg2"], "stage": ["sg3"]}``

``default_elb_securitygroups``
******************************

Comma separated list or json of ELB security groups to include for all
deployments. If a comma separated list is given, the groups are applied to all
environments. If a json is provide, it assigns groups only to the specified
environment.

    | *Required*: No
    | *Example*: ``test_sg,example_elb_sg``
    | *Example (json)*: ``{"dev": ["sg1", "sg2"], "stage": ["sg3"]}``


``default_securitygroup_rules``
*******************************

Security group rules that should be included by default for the application specific group. If `$self` is used as the
security group name, it will self-reference to its own application name.

    | *Required*: No
    | *Example*: ``{ "bastion" : [ { "start_port": "22", "end_port": "22", "protocol": "tcp" } ] }``

``ec2_pipeline_types``
**********************

.. autodata:: foremast.consts.EC2_PIPELINE_TYPES
   :noindex:

``gate_client_cert``
********************

If accessing Gate via x509 certificate authentication, this value provides the
local path to the certificate. Only PEM certs are supported at this time
(containing both the key and certificate in the PEM).

    | *Required*: No
    | *Example*: ``/var/certs/gate-cert.pem``

``gate_ca_bundle``
********************

If accessing Gate via x509 leveraging a custom certificate authority (such as
acting as your own CA), this value provides the local path to the CA bundle. It
is recommended to use an existing CA Bundle and append your CA certificate to it
(https://certifi.io/en/latest/)

    | *Required*: No
    | *Example*: ``/var/certs/CA.pem``

``[credentials]``
~~~~~~~~~~~~~~~~~

Section for handling credential configurations such as tokens, usernames, and
passwords

``gitlab_token``
****************

Gitlab token used for authentication in Foremast

    | *Required*: No

``slack_token``
***************

Slack token used for authentication when sending Slack messages from Foremast

    | *Required*: No


``[whitelists]``
~~~~~~~~~~~~~~~~

Sections for configuring whitelist info

``asg_whitelist``
*****************

Comma delimiated list of applications to whitelist from ASG rules

    | *Required*: No

``[formats]``
~~~~~~~~~~~~~

Section handling the naming convention of applications, elb, iam, s3 buckets and
other services.

The most common sections are shown. The complete list of sections and defaults
are defined by the underlying library gogo-utils_.

Any of the possible variables below can be used as the value.

- ``domain`` organization domain
- ``env`` dev, qa, production, etc
- ``project`` lowercase git group/organization
- ``repo`` lowercase git project/repository
- ``raw_project`` git group/organization
- ``raw_repo`` git project/repository

``domain``
**********

A string of your organization's domain

    | *Default*: example.com
    | *Required*: No

``app``
*******

A string of the format of your application

    | *Default*: {repo}{project}
    | *Required*: No

``dns_elb``
***********

An FQDN of your application's Elastic Load Balancer (ELB)

    | *Default*: {repo}.{project}.{env}.{domain}
    | *Required*: No

``s3_bucket``
*************

An string of your base S3 bucket name

    | *Default*: archaius-{env}
    | *Required*: No

``jenkins_job_name``
********************

An string of the format of the application's jenkins job name

    | *Default*: {project}_{repo}
    | *Required*: No

``[task_timeouts]``
~~~~~~~~~~~~~~~~~~~

Section handling customization of task timeouts when communicating with
Spinnaker. Timeouts can vary per environment and per task.

``default``
***********

The default task timeout value

    | *Default*: 120
    | *Required*: No

``envs``
********

A json object keyed by environment name. Each value should be a json object
keyed by task name.

    | *Default*: 120
    | *Required*: No

.. _gogo-utils: https://github.com/gogoair/gogo-utils#formats
