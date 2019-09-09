.. _advanced_scaling_policy

#######################################
``scaling_policy`` - V1 Cluster Scaling
#######################################

Defines scaling policy to attach to ASG. If this block does not exist, no
scaling policy will be attached.

.. contents::
   :local:

``scaling_policy`` *Examples*
*****************************

   This section contains example usage but you are encouraged to modify and build your own scaling
   configurations that meet your needs.

*Simple CPUUtilization Scaling Example*
=======================================

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

*Custom Scale Up/Down Increments Example*
=========================================

   .. note::  To reduce nodes in a cluster the Scale Down API requires a negative number.

   .. code-block:: json

      {
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
      }

``scaling_policy`` *Keys*
*************************

``metric``
==========

   The CloudWatch metric to trigger auto-scaling events.

      | *Type*: string
      | *Default*: ``"CPUUtilization"``
      | *Options*:

         - ``"CPUUtilization"``
         -  ``"NetworkIn"``
         -  ``"NetworkOut"``
         -  ``"DiskReadBytes"``

``threshold``
=============

   Metrics value limit for scaling up

      | *Type*: int

``scale_down``
==============

   Attach a default scale-down policy

      | *Type*: boolean
      | *Default*: ``true``

``increase_scaling_adjustment``
===============================

   Amount to increment by on scale up policies

      | *Type*: int
      | *Default*: 1

``decrease_scaling_adjustment``
===============================

   Amount to decrement by on scale down policies. Negative numbers represent removing nodes from cluster.

      | *Type*: int
      | *Default*: -1

``period_minutes``
==================

   Time period to look across for determining if threshold was met. If you wish to have seconds, using a 
   floating point such as .5 for 30 seconds.

      | *Type*: float
      | *Default*: 30
      | *Units*: Minutes

``statistic``
=============

   Statistic to calculate at the period to determine if threshold was met

      | *Type*: string
      | *Default*: ``"Average"``
      | *Options*:

         - ``"Average"``
         - ``"Maximum"``
         - ``"Minimum"``
         - ``"Sum"``

``instance_warmup``
===================

   Time period to wait before adding metrics to Auto Scaling group

      | *Type*: int
      | *Default*: 600
      | *Units*: seconds