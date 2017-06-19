.. _getting_started:

======================
Getting Started
======================

.. contents::
    :local:

This getting started guide will walk through the process of using Foremast to create an application in Spinnaker and dynamically generate a basic Spinnaker pipeline.


Getting started with Foremast consists of the following steps:

    1. Setting up configuration files
    2. Installing Foremast
    3. Setting up the variables
    4. Running Foremast

Quick Start Guide
-----------------

In this section, we will install, configure and run Foremast to create a basic pipeline.

Installation
************

Setting up the environment

.. code-block:: sh

    $ pip3 install virtualenv
    $ virtualenv -p $(which python3) venv
    $ source venv/bin/activate

Method 1 - Using pip (Preferred)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: sh

    $ pip install foremast

Method 2 - Using git
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: sh

    $ git clone https://github.com/gogoit/foremast.git
    $ cd foremast
    $ pip3 install -U .

Configuration Files
*******************

Create a ``runway`` and ``.foremast`` directory and go into ``runway`` directory.

.. code-block:: sh

    $ mkdir runway .foremast

Create ``pipeline.json`` in ``runway`` directory

.. code-block:: json

    {
       "deployment": "spinnaker",
       "env": [ "dev"]
    }

Create ``application-master-dev.json`` in ``runway`` directory.

.. code-block:: json

    {
       "app": {
           "instance_type": "t2.micro"
       },
       "asg": {
           "max_inst": 1,
           "min_inst": 1
       },
       "regions": [
           "us-east-1"
       ]
    }

Go to ``.foremast`` directory and create the ``foremast.cfg`` file.

.. code-block:: ini

    [base]
    domain = example.com
    envs = dev,prod
    regions = us-east-1
    gate_api_url = http://gate.example.com:8084


You should now see something similar structure.

.. code-block:: sh

    $ tree -a
    .
    ├── .foremast
    │   └── foremast.cfg
    └── runway
        ├── application-master-dev.json
        └── pipeline.json

    2 directories, 3 files


Running
*******

Now from within the root directory, run ``foremast-pipeline``.

.. code-block:: sh

    $ GIT_REPO=hello PROJECT=world RUNWAY_DIR=runway/ foremast-pipeline

This will create an application in Spinnaker named ``helloworld`` along with a simple pipeline.
