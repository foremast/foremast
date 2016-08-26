.. _ami-lookup.json:

================================
ami-lookup.json
================================

.. contents::
   :local:

Purpose
-------
This json file is used as an AMI ID look up table for each region. It is used during the bake stage of Spinnaker deployments in order to determine the base AMI ID to use for baking.

Example Json
----------------------

.. code-block:: json

    {
        "us-east-1": {
            "origin": "ami-xxxx",
            "origin_default": "ami-xxxx",
            "origin_fedora": "ami-xxxx",
            "origin_amazon": "ami-xxxx",
            "origin_ubuntu": "ami-xxxx",
            "origin_debian": "ami-xxxx",
            "origin_testing": "ami-xxxx",
        }
        "us-west-2": {
            "origin": "ami-xxxx",
            "origin_default": "ami-xxxx",
            "origin_fedora": "ami-xxxx",
            "origin_amazon": "ami-xxxx",
            "origin_ubuntu": "ami-xxxx",
            "origin_debian": "ami-xxxx",
            "origin_testing": "ami-xxxx",
        }
    }


Json Location
------------------------
Foremast will look for this information at ``ami_json_url`` defined in :doc:`foremast_config`. For example, you can host the file named ``ami-lookup.json`` in an S3 bucket and then set ``ami_json_url = http://s3bucketurl.com/ami-lookup.json``.

You can host this file anywhere as long as an HTTP GET will return the JSON and a 2XX.
