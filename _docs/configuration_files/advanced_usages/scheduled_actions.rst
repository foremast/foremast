.. _advanced_scheduled_actions

#####################
``scheduled_actions``
#####################

Defines scheduled actions to perform on an cluster group. You can specify multiple actions
if needed. If this block does not exist, no scheduled actions will be attached.

``scheduled_actions`` *Example*
*******************************

.. code-block:: json

  {
    "scheduled_actions": [
      {
        "recurrence": "1 * * * *", 
        "minSize": 1, 
        "maxSize": 1, 
        "desiredCapacity": 1
      },
      {
        "recurrence": "2 * * * *", 
        "minSize": 2, 
        "maxSize": 2, 
        "desiredCapacity": 2
      }
    ]
  }

``scheduled_actions`` *Keys*
****************************

``recurrence``
============== 

   A valid CRON expression evaluated that is evaluated in UTC.

      | *Type*: string

``minSize``
===========

   Minimum size of Auto Scaling Group

      | *Type*: int

``maxSize``
===========

   Max size of Auto Scaling Group

      | *Type*: int

``desiredCapacity``
===================

   Desired Capacity of Auto Scaling Group

      | *Type*: int