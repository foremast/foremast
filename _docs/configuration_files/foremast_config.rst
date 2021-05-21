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

Specifying a Configuration file
-------------------------------

Optionally, it is possible to specify the location of a configuration file for Foremast to use by 
setting the ``FOREMAST_CONFIG_FILE`` environment variable.  This is useful if you do not store your 
config file in one of the locations listed above, or if you need to toggle between multiple
configuration files to support different configurations.  

Example: A config file for two different Spinnaker Instances

.. code-block:: console

    # Generate pipeline for spinnaker1
    FOREMAST_CONFIG_FILE=config-spinnaker1.py
    foremast generate pipeline
    # Generate pipeline for spinnaker2
    FOREMAST_CONFIG_FILE=config-spinnaker2.py
    foremast generate pipeline



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
Foremast for **AWS**.  See section :ref:`gcp-section` for GCP Environments.

    | *Example*: ``dev,stage,prod``
    | *Required*: Yes

``env_configs`` Keys
********************

    Nested dictionary of environment names along with environment features

        | *Type*: Object
        | *Default*: ``None``
        | *Example Configuration*:

.. code-block:: json

            {
                'env_configs': {
                    "build": {
                        "enable_approval_skip": True
                    },
                    "data": {
                        "enable_approval_skip": False
                    },
                    "media": {
                        "enable_approval_skip": False
                    },
                    "stage": {
                        "enable_approval_skip": True
                    },
                    "prod": {
                        "enable_approval_skip": False
                    },
                    "prodp": {
                        "enable_approval_skip": False
                    }
                }
            }

    ``enable_approval_skip``
    ^^^^^^^^^^^^^^^^^^^^^^^^

        Determines if approval skips are allowed in this environment. Allows admins to ultimately enforce 
        deployment approvals in templates

        | *Type*: boolean
        | *Default*: ``False``

``aws_types``
*************

.. warning::
    `aws_types` replaced `types` beginning in Foremast 5.x when GCP support was added.
    It is recommended to migrate from the deprecated `types` configuration option to the new `aws_types`.

List of foremast managed Pipeline types to allow for AWS deployments

    | *Type*: str
    | *Example*: ``ec2,lambda``
    | *Default*: ``ec2,lambda,s3,datapipeline,rolling``
    | *Required*: No

``gcp_types``
*************

List of foremast managed Pipeline types to allow for GCP deployments

    | *Type*: str
    | *Example*: ``cloudfunction``
    | *Default*: ``cloudfunction``
    | *Required*: No

``aws_manual_types``
******************

.. warning::
    `aws_manual_types` replaced `manual_types` beginning in Foremast 5.x when GCP support was added.
    It is recommended to migrate from the deprecated `manual_types` configuration option to the new `aws_manual_types`.


List of pipeline types that will trigger Foremast's manual pipeline template feature.  When
Foremast Infrastructure features are used the pipeline types listed here will create AWS
infrastructure.  See :ref:`advanced_manual_pipelines` for more details on this feature.

    | *Type*: str
    | *Example*: ``manual,custom_pipeline_name``
    | *Default*: ``manual``
    | *Required*: No

``gcp_manual_types``
******************

List of pipeline types that will trigger Foremast's manual pipeline template feature.  When
Foremast Infrastructure features are used the pipeline types listed here will create GCP
infrastructure. See :ref:`advanced_manual_pipelines` for more details on this feature.

    | *Type*: str
    | *Example*: ``gke,custom_pipeline_name``
    | *Default*: ````
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

``runway_base_path``
******************

Base path to use when looking for custom runway directories. If provided,
Foremast will first look for Foremast runway files in this directory. 
This is useful if you have a different folder or location to store pipeline
configuration values.

    | *Type*: str
    | *Default*: ``runway``
    | *Required*: No

``default_run_as_user``
***********************

Default user to run pipelines as. This is needed for leveraging service accounts in Fiat.

    | *Type*: str
    | *Default*: ``null``
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

``gate_authentication`` Keys
****************************

    Credential Provider Object used to authenticate to Gate

        | *Type*: Object
        | *Default*: ``None``
        | *Example Configuration*:

.. code-block:: json

            {
                'credentials': {
                    'gate_authentication': {
                        'google_iap': {
                            'enabled': False,
                            'oauth_client_id': 'some_id.apps.googleusercontent.com',
                            'sa_credentials_path': '/tmp/google-service-account.json'
                        },
                        'github': {
                            'token': '<GITHUB_TOKEN>'
                        }
                    }
                }
            }

``google_iap`` Keys
*******************

    We currently support in addition to x509, Google Identity Aware Proxy authentication.

    ``enabled``
    ^^^^^^^^^^^

        Determines if this authentication method should be used or not.

        | *Type*: boolean
        | *Default*: ``False``
    
    ``oauth_client_id``

        Application Client ID using Identity Aware Proxy. Can be found in the Google Cloud Console

        | *Type*: string
        | *Default*: ``None``

    ``sa_credentials_path``

        Path to Google Cloud Service Account used to Authenticate to Identity Aware Proxy.
        Must be added to IAP in GCP console to grant permission.

        | *Type*: string
        | *Default*: ``None``

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
keyed by task name.  This section only applies to AWS environments.

    | *Default*: 120
    | *Required*: No

.. _gogo-utils: https://github.com/gogoair/gogo-utils#formats

.. _gcp-section:

``[gcp]``
~~~~~~~~~~~~~

Section handling GCP infrastructure and authentication configuration options.

``envs``
********

A json object keyed by environment name. Each value should be a json object that defines the
GCP environment's structure.  The property `service_account_project` defines which project
is used by Foremast when creating service accounts.  You should use different a `service_account_project` for each
environment to ensure IAM permissions are not granted between environments.  See the page :ref:`gcp_creds` for more info on
setting up GCP credentials for Foremast.

    | *Default*: None
    | *Required*: Yes

Example structure:

.. code-block:: json

            {
                'stage': {
                    'organization': 'your-org.com',
                    'service_account_project': 'project-id-for-creating-service-accounts-stage',
                    'service_account_path': '/path/to/service/account/used/by/foremast-stage.json'
                },
                'prod': {
                    'organization': 'your-org.com',
                    'service_account_project': 'project-id-for-creating-service-accounts-prod',
                    'service_account_path': '/path/to/service/account/used/by/foremast-prod.json'
                },
            }