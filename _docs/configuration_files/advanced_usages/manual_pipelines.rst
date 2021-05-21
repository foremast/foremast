.. _advanced_manual_pipelines

################
Manual Pipelines
################

  Manual Pipelines allow users of Foremast to take raw Spinnaker Pipeline JSON and apply it via Foremast (thus version controlling
  their pipelines). This is useful for pipeline types in which Foremast is still adding support for. This is also
  an unopinionated interface to create templated Spinnaker pipelines using standard Jinja2.

  .. contents::
    :local:

Getting a Spinnaker Pipeline's JSON Body
****************************************

  Spinnaker Pipelines are extremely customizable, extensible, and complex. The easiest way to create a Spinnaker Pipeline
  is to create one via the UI manually first! 

  1. Create your ideal pipeline via Spinnaker UI; valid, required stages, fully configured.
  2. From the Pipeline Configuration Page, Click `Pipeline Actions` and select `Edit as JSON`.
  
  .. image:: ../../_static/helper-manual-pipelines-spinnaker-edit-as-json.png

  3. Store JSON in a file in ``RUNWAY_DIR``; name it whatever you need

  .. image:: ../../_static/helper-manual-pipelines-spinnaker-json.png

``pipeline.json`` *Example*
***************************

  .. note::  | The below example uses templated pipeline files managed inside of ``TEMPLATES_PATH``. To specify a remote path, prefix a file name with: ``"templates://"``.
             |
             | This enables Foremast users to specify common base templates for manual pipelines reducing duplicate templates in repositories.
             |
             | In addition, this example is passing in some variables for use in the Jinja2 template using ``"template_variables"``.

  .. code-block:: json

    {
        "deployment": "spinnaker",
        "type": "manual",
        "pipeline_files": [
            "templates://manual-pipeline.json.j2"
        ],
        "template_variables": [
            {
                "foo": "bar",
                "REGION": "us-west3"
            }
        ]
    }

``pipeline.json`` *Keys*
**********************************

``pipeline_files``
==================

  .. note::  | Files could be of type ``*.json`` to denote a standard JSON document or files could be of type ``*.json.j2`` to denote Jinja2 template.
             |
             | In addition, remote templates can be leverage by stating ``"templates://"`` URI. Foremast will look within the ``"TEMPLATES_PATH"`` specified in `config.py` for remote pipeline files.
  
  List of JSON files to use for ``"manual"`` pipelines. 

      | *Type*: Array
      | *Default*: ``[]``

``template_variables``
======================

  List of key/value pair objects to feed into templates. See below example on usage.

      | *Type*: Array of Objects
      | *Default*: ``[]``
      | *Example Options*:

         *pipeline.json*

         .. code-block:: json

            {
               "template_variables": [
                  {
                        "key": "value",
                        "region": "us-west-2",
                        "owner_email": "foo@example.com"
                  }
               ]
            }

         *manual-jinja-example.json.j2*
         
         .. code-block:: json

            [{
                "schema" : "v2",
                "locked": {
                  "allowUnlockUi": false,
                  "ui": true
                },
                "protect": false,
                "metadata": {
                    "name": "{{ template_variables.key }}",
                    "description": "Deploys code to {{ template_variables.region }}",
                    "owner": "{{ template_variables.name }}",
                    "scopes": ["global"]
                }
                "pipeline": {},
                "triggers": []
            }]

Formatting your pipeline template file
****************************************

Your pipeline template file should return an array with 1 or more Spinnaker pipeline definitions. 
Using an array allows Foremast to support the creation of more than one pipeline using
a single pipeline template file.  The most common usecase for this is creating
two pipelines that are dependent on eachother, for example one pipeline that triggers when
another finishes running.  If only one pipeline is desired you should still use an array, but 
only place one Spinnaker pipeline definition in the array.

*multiple-pipelines-jinja-example.json.j2*
         
  .. code-block:: json

    [{
        "name" : "The first pipeline",
        "schema" : "v2",
        "locked": {
          "allowUnlockUi": false,
          "ui": true
        },
        "protect": false,
        "metadata": {
            "name": "{{ template_variables.key }}",
            "description": "Deploys code to {{ template_variables.region }}",
            "owner": "{{ template_variables.name }}",
            "scopes": ["global"]
        }
        "pipeline": {},
        "triggers": []
    },{
        "name" : "The second pipeline",
        "schema" : "v2",
        "locked": {
          "allowUnlockUi": false,
          "ui": true
        },
        "protect": false,
        "metadata": {
            "name": "{{ template_variables.key }}",
            "description": "Deploys code to {{ template_variables.region }}",
            "owner": "{{ template_variables.name }}",
            "scopes": ["global"]
        }
        "pipeline": {},
        "triggers": []
    }]

  .. note::   | `template_variables` are shared per file.  Multiple Spinnaker pipelines defined in 
              | a single file are sharing a common set of variables