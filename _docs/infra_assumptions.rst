================
Infrastructure
================

.. contents::
   :local:

Spinnaker
---------

- Foremast assumes that Spinnaker is already setup. Please see the `Spinnaker documentation`_ for assistance
- Requires connectivity to the Gate component of Spinnaker. Foremast does not support authentication on Gate (yet).
- Assumes AWS EBS is used for Packer bakes in Spinnaker Rosco


Spinnaker Component Versions
****************************
Below are the Spinnaker component versions that we use internally at Gogo and that Foremast has been tested against:

    - Gate: ``2.70.0``
    - Clouddriver: ``1.212.0``
    - Deck: ``2.711.0``
    - Igor: ``1.50.0``
    - Echo: ``1.108.0``
    - Front50: ``1.8.0``
    - Spinnaker: ``0.50.0``
    - Rosco: ``0.42.0``
    - Orca: ``1.168.0``

If you have any issues with Foremast at other Spinnaker versions please file an issue (or pull request).

AWS
---

Foremast only works with AWS (for now). Below are the AWS requirements:

- Foremast IAM Access:

  - Will need credentials set up in a Boto3 configuration file. See :doc:`aws_creds` for details.

  - IAM user or role will need the following permissions:

    - ``S3``: View, create and delete buckets.

    - ``IAM``: View, create and  delete roles, uers, and policies.

    - ``Route53``: View, create, and delete DNS records.

  - Everything else, such as ELBs and security groups, are handled through Spinnaker.

- VPC Subnets

  - If new subnets are being setup, follow the `Spinnaker AWS Setup guide`_.

  - If using existing subnets add an ``immutable_metadata`` tag.

    - Example ``immutable_metadata`` tag: ``{"purpose": "external", "target": "elb"}``

    - The  ``"purpose"`` key will dictate how this appears in Spinnaker. 

      - Needs to be ``"internal"`` or ``"external"`` in order to properly work with Foremast

Jenkins
-------

Foremast takes advantage of the Spinnaker Jenkins stage. In order for the Foremast generated pipeline to work you will need the following:

- Jenkins configuration named "JenkinsCI" in Spinnaker Igor

  - Example Igor config::

        jenkins:
          Masters:
            -
              name: 'JenkinsCI' # The display name for this server
              address: 'http://jenkinsci.example.com'
              username: 'spinnaker'
              password: 'password'

Necessary Jenkins Jobs
***********************

The default generated pipeline requires a couple of Jenkins jobs to be setup in order to run.

- ``pipes-pipeline-prepare``

  - Runs Foremast ``prepare-infrastructure`` during the "Infrastructure Setup" pipeline stage

  - Requires the following string variables

    - ``PROJECT``

    - ``GIT_REPO``

    - ``ENV``

    - ``REGION``

  - Example Shell after cloning Foremast::

     virtualenv -p python3 venv
     . venv/bin/activate
     pip install -U --quiet .

     prepare-infrastructure

- ``pipes-scaling-policy``

  - Runs Foremast ``create-scaling-policy`` for attaching a scaling policy if defined.

  - Only necessary if you plan on attaching scaling policies

  - Requires the following string variables

    - ``PROJECT``

    - ``GIT_REPO``

    - ``ENV``

    - ``REGION``

  - Example Shell after cloning Foremast::

     virtualenv -p python3 venv
     . venv/bin/activate
     pip install -U --quiet .

     create-scaling-policy

Gitlab
------

Gitlab is not required for Spinnaker but if it is already part of your infrastructure you can have Foremast directly look up the :doc:`pipeline_json` and :doc:`application_json` files. You will need to get the Gitlab Token of a user that has permissions to the desired repository and set them in your :doc:`foremast_config`. 

.. _`Spinnaker documentation`: http://www.spinnaker.io/docs
.. _`Spinnaker AWS Setup guide`: http://www.spinnaker.io/v1.0/docs/target-deployment-setup#section-amazon-web-services-setup
