==============================
Deploy Spinnaker Using Halyard
==============================

Run Spinnaker using Halyard to deploy Services to a Kubernetes Cluster. For more
information about Spinnaker, see :ref:`halyard-overview`.

.. toctree::
   :maxdepth: 2
   :titlesonly:
   :glob:

   *

------------
Requirements
------------

* Docker
* Kubernetes configuration file

-------
Running
-------

Launch the Halyard daemon and drop into a prompt with
:download:`launch_daemon.bash <launch_daemon.bash>`. It mounts the Host
directory :file:`hal` without a dot prefix to :file:`/home/spinnaker/.hal/`
inside the Halyard Container. This is so the directory is more visible outside
of the Container.

.. code-block:: bash

   export KUBECONFIG=/fully/qualified/path/to/.kube/config
   ./launch_daemon.bash

Show the configuration that will be deployed:

.. code-block:: bash

   hal version list
   hal config
   hal config --help  # Explore and set configurations
   hal deploy apply

Run the post deployment definition to clean up the bootstrap Pods with
:download:`post-deploy.yml <post-deploy.yml>`.

.. code-block:: bash

   export KUBECONFIG=/fully/qualified/path/to/.kube/config
   kubectl apply --filename post-deploy.yml

--------------
Update Version
--------------

.. code-block:: bash

   hal version list
   hal config version edit --version ${NEW_VERSION}
   hal deploy apply
