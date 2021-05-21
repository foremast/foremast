###################################
Configuration Files Advanced Usages
###################################

Manual Pipelines
****************

    While Foremast has great support for many Spinnaker deployment features, it is not without flaws. Most
    noteably, Foremast struggles in a few areas:

    1. Limited support outside of AWS based pipelines
    2. Keeping up with new features released in Spinnaker
    3. Pipelines, Deployment Flows, and Structure can be seen as opinionated at times

    While the Foremast's templating engine built around `Jinja2 <https://jinja.palletsprojects.com/>`_ is rather 
    extensible, there is a bit of boilerplate code that needs to be written to support custom pipelines. This 
    leads to many Foremast users not being able to Foremast to support new and/or more complex requirements 
    not defined within Foremast just yet. 

    Regardless, we are still left with a need for a solution to manually creating pipelines via the Spinnaker UI. 
    As a result, we have support in Foremast to allow users to specify `"manual"` pipeline type. 
    
    Manual pipelines allow users to store Spinnaker Pipeline JSON in a `RUNWAY_DIR` and allow Foremast 
    to create/manage Spinnaker Pipelines using native Spinnaker Pipeline JSON. In addition, we enable the ability to 
    store the JSON body as a Jinja2 Template (`json.j2`), allowing users to pass custom variables defined in Foremast 
    configuration files to override common fields in Spinnaker Pipeline JSON.

    While not ideal, this helps create support for things otherwise not currently supported in Foremast such as 
    Kubernetes, AWS ECS, Google Cloud Functions, etc. More importantly it helps solve some of the issues noted above:

    1. Spinnaker JSON + Foremast Templating = PROFIT
    2. Create via Spinnaker UI, store the raw Spinnaker Pipeline JSON, Foremast does the heavy lifting of management
    3. Unopinonated and Foremast only manages creation of pipelines (only acts as a template engine if specified)

    To enable manual pipelines, a few top level `"pipeline"` keys are needed.
    
    .. toctree::
      :maxdepth: 2

      manual_pipelines

Cluster Scaling Policies
************************

    Foremast Scaling Policies have two implementations:

    1. A Foremast Managed Implementation (v1) - ``scaling_policy``
    2. A Custom Spinnaker Implementation (v2) - ``custom_scaling_policies``

    The intentions behind the scaling policy v1 implementation is that users
    of Foremast could simplify the complexities of scaling policies to end 
    users. As a result, users could only specify their ``scale_up`` and 
    ``scale_down`` fields.

    With many recent enhancements and features in Spinnaker's API, we realized
    that some advanced users would prefer a more advanced implementation enabling
    teams to specify things like custom scaling policies leveraging custom metrics
    in their respective cloud provider. In addition, some teams have complex scaling
    policies that involve multiple steps. Finally, we wanted an unopinionated 
    implementation that is true to the Spinnaker experience. As a result, the scaling
    policy v2 implementation was created.

    In order to maintain support for both simple scaling policies, as well as advanced
    custom scaling policies, we have broken the implementation into two top level keys.

    .. note::  When leveraging scaling policies in Foremast **only** one of the two implementations can be used.

            If both ``scaling_policy`` and ``custom_scaling_policies``, behavior will default to v1 ``scaling_policy``
            for backwards compatibility.

    .. toctree::
      :maxdepth: 2

      scaling_policy
      custom_scaling_policies

Scheduled Actions
*****************

    Scheduled Actions are useful for scaling clusters on time based events such as provisioning shadow capacity, preparing for large 
    large spikes (such as email campaigns, promotions, holidays/sales, etc) and also deprovisioning (post spike). These operations
    work based on simple CRON expressions, making them easy to implement.

    .. note::  Scheduled Actions persist between clusters as they are done at the service level. As a result, ensure you
               delete scheduled actions manually via the Spinnaker UI if you remove them from Foremast configuration files.

    .. toctree::
      :maxdepth: 2

      scheduled_actions

Foremast Provider Tags
**********************

    Foremast has the ability to perform a lot of important infrastructure actions, but Foremast is currently not stateful. This
    can cause issues with certain provider APIs that require some state (such as AWS S3 PutBucketNotification). In addition,
    some users may wish to restrict Foremast from making changes on specific resources. To address this, Foremast can leverage
    Tags/Labels to restrict some operations. 

    .. toctree::
      :maxdepth: 2

      foremast_tags

GCP Service Account IAM Policies
*********************************

    .. toctree::
      :maxdepth: 2

      gcp_svc_account_iam_policies
