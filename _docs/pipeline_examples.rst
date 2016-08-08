==========================
Pipeline Flow and Examples
==========================

.. contents::
   :local:

Foremast generates a single pipeline per region. The pipeline is designed to allow deploying to multiple environment with checkpoints between each transition.

Default Pipeline Flow
---------------------

The below flow can repeat for as many environments as defined in the configs. At Gogo, most applications go through these stages 3 times as we deploy to dev, stage, and production.

1. Configuration

  - This stages defines the Jenkins trigger, property files, and pipeline-wide notifications

2. Bake

  - Bakes an AMI the specified AMI ID

3. Infrastructure Setup [$env]

  - Calls a Jenkins job to run the ``prepare-infrastructure`` Foremast command against a specific account.
  - Setups AWS infrastructure such as ELB, IAM roles, S3 bucket, and DNS needed for an application

4. Deploy $env

   - Uses Spinnaker to create a cluster and server group in specific account.
   - The behavior of this stage is largely based on the :doc:`application_json` configs.

5. Attach Scaling Policy [$env]

  - If a scaling policy is defined in :doc:`application_json`, attaches it to the deployed server group
  - If no policy is defined, this stage is excluded

6. Checkpoint $next-env

  - A manual checkpoint stage. This requires human intervention to approve deployment to the next environment.


Stages 3-6 repeat for each environment/account defined in :doc:`pipeline_json`.

.. image:: _static/minimal-pipeline-example.png

The default generated pipeline should look like the above image. This is the basic `bake` -> `infrastructure` -> `deploy` -> `checkpoint` pipeline described above.

Custom Pipelines
----------------

You can specify an external templates directory in :doc:`foremast_config`. Templates in an external directory will need to have the same directory structure and naming as the default templates. if `templates_path` is set in :doc:`foremast_config`, Foremast will first see if the file exists there. If not, it will fall back to the provided tempaltes.

If you need to add more stages or  change the defaults, this is all possible via external templates. Please the `foremast-templates repo`_ for examples on the templates.


Example Workflow
-----------------

At Gogo we have a detailed workflow for using Foremast internally. Feel free to copy our workflow or use it as insperation for your own. You can view all of our internal templates on the `foremast-templates repo`_.

.. image:: _static/gogo-pipeline.png

#. the :doc:`application_json` and :doc:`pipeline_json` are bundled directly with the application code

#. Developer makes a change to one of those configs and pushes to the application's git repository

#. A server-side git hook detects a change and triggers a Jenkins job to run Foremast ``prepare-app-pipeline`` This regenerates the application and pipeline in Spinnaker

#. The application artifacts are build using a Jenkins job and stored as an RPM

#. Spinnaker triggers detect a completed Jenkins jobs and starts a new deployment pipeline

    #. Bakes an AMI using build RPM

    #. Runs a Jenkins job to run Foremast ``prepare-infrastructure``. This builds out the AWS ELB, SG, S3 bucket, and IAM roles

    #. Runs a Jenkins jobs to tag the effected git repository with AMI info

    #. Deploys the generated AMI to desired environments

    #. Runs QE/QA checks against deployed application

    #. Tags the repository with deployment information

    #. Attaches defined scaling policies

    #. Wants for manual judgement before continuing to the next stage


.. _`foremast-templates repo`: https://github.com/gogoair/foremast-templates
