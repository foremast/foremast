.. _gcp_creds:

===============
GCP Credentials
===============

.. contents::
   :local:

Purpose
-------

This is how AWS credentials are stored for usage with Foremast. All AWS calls
outside of Spinnaker use Boto3 so standard Boto3 locations work but
account/environment must be specified.

This section explains how GCP credentials are stored for usage with Foremast.  All GCP
calls outside of Spinnaker use the official GCP Python Clients and service account authentication.

Example Configuration
---------------------

See the GCP Configuration section for details: :ref:`gcp-section`

Service Account Basics
------------------------------

Each GCP environment defined in Foremast needs a path to a json service account.  You can
export these from GCP's IAM Console.  Foremast will only modify one GCP environment at a time, meaning
when a pipeline is running for env1, env2 will not be modified.  **We recommend using a different service
account per environment (with limited permissions) as an additional step to ensure security and proper segmentation
of environments.**


Service Account Permissions
-----------------------------

Permissions needed by Foremast can vary on a project-by-project basis.  You can set these up for each
individual project, or use folders and org level IAM policies to assign permissions across multiple projects.

**Minimum Permissions:**

Project IAM Admin (`roles/resourcemanager.projectIamAdmin`) is required in all projects for Foremast
to get and set IAM permissions.