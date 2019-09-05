###################################
Configuration Files Advanced Usages
###################################

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