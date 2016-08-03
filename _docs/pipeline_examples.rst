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

Custom Pipelines
----------------

You can specify an external templates directory in :doc:`foremast_config`. Templates in an external directory will need to have the same directory structure and naming as the default templates. if `templates_path` is set in the configs, Foremast will first see if the file exists there. If not, it will fall back to the provided tempaltes.

If you need to add more stages or  change the defaults, this is all possible via external templates. Please see GITLAB_URL for examples on the templates.


Pipeline Examples
-----------------
.. image:: _static/minimal-pipeline-example.png


The default generated pipeline should look like the above image. This is the basic `bake` -> `infrastructure` -> `deploy` -> `checkpoint` pipeline described above.





