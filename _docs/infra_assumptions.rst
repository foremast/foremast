==============
Infrastructure
==============

.. contents::
   :local:

Spinnaker
---------

- Foremast assumes that Spinnaker is already setup. Please see the `Spinnaker
  documentation`_ for assistance
- Requires connectivity to the Gate component of Spinnaker. Foremast also
  supports x509 authentication on Gate.
- Assumes AWS EBS is used for Packer bakes in Spinnaker Rosco

Spinnaker Component Versions
****************************

Previously, we used to publish internally tested versions. We have since moved
to leveraging the release cadence set forth by the Spinnaker community. For more
info around the Spinnaker release cadence, refer to the official can be found 
`Spinnaker Release Cadence`_ page.

For the latest releases of Spinnaker, check out the official `Spinnaker Release 
Versions`_ page.

If you have any issues with Foremast on the latest Spinnaker version, please file an
issue (or pull request).

AWS
---

Foremast only works with AWS (for now). Below are the AWS requirements:

AWS VPC Subnet Tags/Names
*************************

  .. note::  This is a general Spinnaker requirement when working with VPCs

  - If new subnets are being setup, follow the `Spinnaker AWS Setup guide`_.
  - If using existing subnets add an ``immutable_metadata`` tag.

    - Example ``immutable_metadata`` tag: ``{"purpose": "external", "target": "elb"}``
    - The ``"purpose"`` key will dictate how this appears in Spinnaker.

      - Needs to be ``"internal"`` or ``"external"`` in order to properly work with Foremast

Foremast IAM Infrastructure
***************************

  - A general IAM user/role will be needed for Foremast to work. In addition,
    Foremast will need credentials set up in a Boto3 configuration file. See
    :ref:`aws_creds` for details.

  - Spinnaker handles the updates for things such as ELBs and security groups.

Foremast IAM Policy
*******************

  .. warning:: The IAM Policy found below is a very generic policy for generic usage. 
               You can and **should** consider locking down further using specific 
               resource policies!

  .. literalinclude:: iam-foremast.json
    :language: JSON

Jenkins
-------

Foremast takes advantage of the Spinnaker Jenkins stage. In order for the
Foremast generated pipeline to work you will need the following:

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
**********************

The default generated pipeline requires a couple of Jenkins jobs to be setup in
order to run.

- ``pipes-pipeline-prepare``

  - Runs Foremast ``prepare-infrastructure`` during the "Infrastructure Setup"
    pipeline stage

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

  - Runs Foremast ``create-scaling-policy`` for attaching a scaling policy if
    defined.

  - Only necessary if you plan on attaching scaling policies

  - Requires the following string variables

    - ``PROJECT``

    - ``GIT_REPO``

    - ``ENV``

    - ``REGION``

  - Example Shell after cloning Foremast

    .. code-block:: bash

       virtualenv -p python3 venv
       . venv/bin/activate
       pip install -U --quiet .

       create-scaling-policy

       # You can export these variables or also pass them beforehand such as:
       export GIT_REPO=<repo_name>
       export ENV=<spinnaker_env_name>

       PROJECT=<repo_project> RUNWAY_DIR=<OS_path_to_runway_dir> \
          REGION=<spinnaker_env_region> \
          foremast-infrastructure

Gitlab
------

Gitlab is not required for Spinnaker but if it is already part of your
infrastructure you can have Foremast directly look up the :ref:`pipeline_json`
and :ref:`application_json` files. You will need to get the Gitlab Token of a
user that has permissions to the desired repository and set them in your
:ref:`foremast_config`.

.. _`Spinnaker documentation`: https://www.spinnaker.io/concepts/
.. _`Spinnaker AWS Setup guide`: https://www.spinnaker.io/setup/install/providers/aws/
.. _`Spinnaker Release Versions`: https://www.spinnaker.io/community/releases/versions/
.. _`Spinnaker Release Cadence`: https://www.spinnaker.io/community/releases/release-cadence/
