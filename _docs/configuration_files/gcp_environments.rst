.. _gcp_environments:

=================
GCP Environments
=================

.. contents::
   :local:

Purpose
--------

This document outlines how to define GCP environments in Foremast and the necessary configuration in GCP.

Definition of GCP Environment
------------------------------

Foremast uses environments with names dev, stage, prod, etc. when deploying and configuring applications.  In AWS
an environment maps to a single AWS account (or sub-account).  GCP does not have a similar concept, and instead resources
are organized within individual projects.  Permissions can be managed at the project level (or higher using inheritance).

How projects in GCP are managed vary by organization.  You may have a single project for each environment like yourcompany-prod
and yourcompany-stage, or you may define projects by teams like yourcompany-yourteam-prod yourcompany-yourteam-stage.  Further,
you may have a strict project naming convention or no convention at all.  You may use folders to define environments, teams, or no folders
at all.

To support any combination of these variables Foremast defines an environment in GCP as a grouping of one or more projects using GCP
project labels.  GCP allows key/value pairs to be added to any project as a label, which Foremast can then easily query.

GCP Project Labels
------------------------------

``foremast_enabled``
********************

When true, Foremast will consider this project when updating permissions and deploying applications.

    | *Default*: None
    | *Required*: Yes
    | *Values*: true or false

``cloud_env``
********************

The name of the environment this project belongs to.

    | *Default*: None
    | *Required*: Yes
    | *Values*: Any string value, must match a GCP Environment defined in Foremast

``foremast_groups``
********************

A `__` (double underscore) separated list of groups that can request permissions to this project.
(See :ref:`gcp_environments_permissions` for details)

    | *Default*: None
    | *Required*: No
    | *Values*: Double underscore separated list of Gitlab or GitHub groups


How to Label a Project in GCP
-------------------------------

Labeling a project is done via the GCP Console or `gcloud` CLI tool.  `See the GCP docs
<https://cloud.google.com/resource-manager/docs/creating-managing-projects#console_3>`_ on managing projects for details.

.. _gcp_environments_permissions:

Controlling Permissions on Projects
------------------------------------

Foremast will not grant permissions between projects with different `cloud_env` values, but Foremast can
grant permissions between projects within the same environment (and does by default).

To ensure certain apps deployed via Foremast cannot request permissions in certain projects, you can use the
`foremast_groups` label and pass in a double underscore separated list of groups permitted to access the project.

For example, assume you have two groups in Gitlab or Github: purchasing and customersupport.  Each team also has
their own GCP Projects: purchasing-prod and customersupport-prod.  If there is no valid use-case for customersupport
applications to request permissions to the purchasing-prod project, the label `foremast_groups=purchasing` can be added.
This ensures only applications in the group purchasing can request permissions on this GCP project.  To support
multiple groups, simply add a double underscore and the additional group names: `foremast_groups=purchasing__anothergroup__anothergroup2`.
If a customersupport application requests permissions to purchasing-prod, Foremast will raise an exception before any
permissions/IAM modifications are made.

This allows Foremast administrators to lock down IAM permissions during deployments when needed.  If `foremast_groups`
is not set or has an empty value, any deployment in Foremast can request permissions to the given project.
