=============
pipeline.json
=============
Purpose
-------
This configuration file is used for defining pipeline settings that affect the pipeline as a whole, not a specific account/environment.

Example Configuration
---------------------
::

    {
    "owner_email": "",
    "documentation": "",
    "notifications": {
        "email": "",
        "slack": ""
        },
    "promote_restrict": "none",
    "base": "tomcat8",
    "env": ["stage", "prod"],
    "image": {
        "root_volume_size": 6
        }
    }


Configuration Elements
----------------------
+-------------------+------------------------------+------------------------+
| Config Key        | Purpose                      | Example                |
+===================+==============================+========================+
| "owner_email"     | Identify who owns an app     | "owner@example.com"    |
+-------------------+------------------------------+------------------------+
| "documentation"   | Link to app documentation    | ""                     |
+-------------------+------------------------------+------------------------+
| "notifications"   | Where pipeline notifications |                        |
+-------------------+ should be sent to (email,    +------------------------+
|    "email"        | or slack)                    | "team@example.com"     |
+-------------------+                              +------------------------+
|    "slack"        |                              | "#team-channel"        |
+-------------------+------------------------------+------------------------+



