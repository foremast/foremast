.. _gcp_svc_account_iam_policies

####################################
GCP Service Account IAM Policies
####################################

This section shows how to apply a default IAM Policy for a service account during the Foremast infra step and Google Cloud Platform.

In GCP a service account has its own IAM Policy.  *This policy is not used to grant the service account access to other resources.*  Instead the
policy is used to determine what users or service accounts can access the service account the IAM Policy is assigned to.  This is rarely necessary
and by default a service account's IAM policy is empty.  One use-case for updating this a service account's policy is
`GKE Workload Identity <https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity>`_.

.. warning::
  Foremast uses a Jinja template to update the service account's IAM policy.  Any existing bindings in the policy will be overwritten, including any manual
  changes made outside of Foremast.

Create the Jinja Template file
***********************************

Create a Jinja template at your Foremast Templates path: `infrastructure/iam/gcp-service-account.json.j2` which outputs an array of GCP role bindings.
Several examples are available below.

Foremast will react differently depending on the output of the rendered Jinja template:

1. If only whitespace is output Foremast will not update the service account's IAM Policy.  This allows the template to only be used for certain pipeline types.
2. If an array of bindings is output, Foremast will update the service accounts IAM Policy bindings using the outputted array of bindings.

Jinja Template Variables
***********************************

The following arguments are given to the Jinja template:

``app``
=================================================

  Name of the app being deployed

      | *Type*: string
      | *Example*: ``myappmygroup``, ``otherappothergroup``

``repo``
=================================================

  Repo name of the app being deployed

      | *Type*: string
      | *Example*: ``myapp``, ``otherapp``

``group``
=================================================

  Group of the app being deployed

      | *Type*: string
      | *Example*: ``dogfood``, ``team5``

``env``
=================================================

  Environment name the service account belongs too

      | *Type*: string
      | *Example*: ``stage``, ``prod``

``pipeline_type``
=================================================

  The type of pipeline being deployed

      | *Type*: string
      | *Example*: ``cloudfunction``, ``manual``

Example: Simple json example
*************************************

.. code-block:: json

    [
       {
          "members": [
             "serviceAccount:my-project.svc.id.goog[coolgroup/coolapp]"
          ],
          "role": "roles/iam.workloadIdentityUser"
       }
    ]

Example: Conditional based on pipeline type
*********************************************

If you only want to update the policy for service accounts in some pipeline types, you can use Jinja if statements to only
output json for certain pipeline types.  If no json is output (i.e. only whitespace) from the template Foremast will not
overwrite the service accounts IAM policy.  This allows you to conditionally use this feature based on inputs.

.. code-block:: json

    {% if pipeline_type == 'manual' %}
    [
       {
          "members": [
             "serviceAccount:my-project.svc.id.goog[coolgroup/coolapp]"
          ],
          "role": "roles/iam.workloadIdentityUser"
       }
    ]
    {% endif %}

Troubleshooting Service Account IAM Policies
*********************************************

Currently the Google Cloud Console does not show service accounts IAM polices.  If you need to verify a policies contents you can use the following command:

.. code-block:: bash

  gcloud iam service-accounts get-iam-policy 'my-svc-account@my-project.iam.gserviceaccount.com'
