*************************
Foremast Scaling Policies
*************************

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

``scaling_policy``
******************

Defines scaling policy to attach to ASG. If this block does not exist, no
scaling policy will be attached

``scaling_policy`` *Keys*
^^^^^^^^^^^^^^^^^^^^^^^^^

``metric`` : The CloudWatch metric to trigger auto-scaling events.

   | *Type*: string
   | *Default*: ``"CPUUtilization"``
   | *Options*:

      - ``"CPUUtilization"``
      -  ``"NetworkIn"``
      -  ``"NetworkOut"``
      -  ``"DiskReadBytes"``

``threshold`` : Metrics value limit for scaling up

   | *Type*: int

``scale_down`` : Attach a default scale-down policy

   | *Type*: boolean
   | *Default*: ``true``

``increase_scaling_adjustment`` : Amount to increment by on scale up policies
   | *Type*: int
   | *Default*: 1

``decrease_scaling_adjustment`` : Amount to decrement by on scale down policies. Negative numbers represent removing nodes from cluster.
   | *Type*: int
   | *Default*: -1

``period_minutes`` : Time period to look across for determining if threshold was
met. If you wish to have seconds, using a floating point such as .5 for 30 seconds.

   | *Type*: float
   | *Default*: 30
   | *Units*: Minutes

``statistic``: Statistic to calculate at the period to determine if threshold
was met

   | *Type*: string
   | *Default*: ``"Average"``
   | *Options*:

      - ``"Average"``
      - ``"Maximum"``
      - ``"Minimum"``
      - ``"Sum"``

``instance_warmup`` : Time period to wait before adding metrics to Auto Scaling group

   | *Type*: int
   | *Default*: 600
   | *Units*: seconds

``scaling_policy`` *Example*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: json

   {
       "scaling_policy": {
           "metric": "CPUUtilization",
           "threshold": 90,
           "period_minutes": 10,
           "instance_warmup": 180,
           "statistic": "Average",
           "scale_down": true
       }
   }

``scaling_policy`` *Custom Scale Up/Down Increments Example*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::  To reduce nodes in a cluster, the Scale Down API requires a negative number.

.. code-block:: json

    "scaling_policy": {
      "metric": "CPUUtilization",
      "threshold": 50,
      "period_minutes": 1,
      "instance_warmup": 120,
      "statistic": "Average",
      "scale_down": true,
      "increase_scaling_adjustment": 5,
      "decrease_scaling_adjustment": -1
    }


``custom_scaling_policies``
***************************

.. warning:: This is for advanced usage and expects understanding of how Spinnaker's API works.

Enables the ability to define custom Spinnaker Cluster Scaling Policies,
as defined by the Spinnaker API. This enables support for multiple scaling 
policies as well as custom metrics using Provider metrics. Currently, only
tested with AWS AutoScaling groups.




``custom_scaling_policies`` *Example*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: json

   {
       "scaling_policy": {
           "metric": "CPUUtilization",
           "threshold": 90,
           "period_minutes": 10,
           "instance_warmup": 180,
           "statistic": "Average",
           "scale_down": true
       }
   }

``custom_scaling_policies`` *Step Scaling Example*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::  This policy adds 1 instance between 75-85% CPU, 3 instances between 85-95, and 5 instances over 95% after 3 evaluation_periods of 1 minute.

.. code-block:: json
   {
      "custom_scaling_policies": [
         {
            "scaling_type": "step_scaling",
            "instance_warmup": 300,
            "scaling_metric": {
               "metric_name": "CPUUtilization",
               "namespace": "AWS/EC2",
               "comparison_operator": "GreaterThanThreshold",
               "evaluation_periods": 3,
               "evaluation_period": 60,
               "threshold": 75,
               "statistic": "Average"
               "dimensions": [
                  {
                        "name": "AutoScalingGroupName",
                        "value": "self"
                  }
               ],
               "steps": [
                  {
                     "scalingAdjustment": 1,
                     "metricIntervalUpperBound": 10,
                     "metricIntervalLowerBound": 0
                  },
                  {
                     "scalingAdjustment": 3,
                     "metricIntervalUpperBound": 20,
                     "metricIntervalLowerBound": 10
                  },
                  {
                     "scalingAdjustment": 5,
                     "metricIntervalLowerBound": 20
                  }
               ]
            },
            "disable_scale_in": false
         }
      ]
   }

.. code-block:: json

    "scaling_policy": {
      "metric": "CPUUtilization",
      "threshold": 50,
      "period_minutes": 1,
      "instance_warmup": 120,
      "statistic": "Average",
      "scale_down": true,
      "increase_scaling_adjustment": 5,
      "decrease_scaling_adjustment": -1
    }

``custom_scaling_policies`` *Target Tracking Example*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: json

    "scaling_policy": {
      "metric": "CPUUtilization",
      "threshold": 50,
      "period_minutes": 1,
      "instance_warmup": 120,
      "statistic": "Average",
      "scale_down": true,
      "increase_scaling_adjustment": 5,
      "decrease_scaling_adjustment": -1
    }
