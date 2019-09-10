.. _halyard-overview:

===============================
Overview of Halyard Conventions
===============================

Quick commands:

.. code-block:: bash

   # Deploy full Spinnaker in rolling fashion starting with bootstrap Services
   hal deploy apply

-------------
Service Names
-------------

Type list in
https://github.com/spinnaker/halyard/blob/master/halyard-deploy/src/main/java/com/netflix/spinnaker/halyard/deploy/spinnaker/v1/service/SpinnakerService.java.

* clouddriver-bootstrap
* `clouddriver <https://github.com/spinnaker/clouddriver>`_
    * Interfaces with all Cloud Providers: AWS, Kubernetes, etc.
* consul-client
* consul-server
* `deck <https://github.com/spinnaker/deck>`_
    * Web UI served by Apache 2 by default
    * Talks directly to Gate for all information
* `echo <https://github.com/spinnaker/echo>`_
* `fiat <https://github.com/spinnaker/fiat>`_
* `front50 <https://github.com/spinnaker/front50>`_
* `gate <https://github.com/spinnaker/gate>`_
    * Main entry point for every API call
    * The web UI makes calls to this API directly, which is why it needs to be
      publicly accessible
    * Makes backend calls to all Spinnaker Services
* `igor <https://github.com/spinnaker/igor>`_
    * Interfaces with Continuous Integration (CI) Providers: Jenkins
    * Stores credentials for Git Repository Providers: GitHub
    * Scans for changes to trigger Pipelines
* `kayenta <https://github.com/spinnaker/kayenta>`_
    * Service introduced into mainline version 1.7.0
    * Provides Automated Canary Analysis (ACA)
* `monitoring-daemon <https://github.com/spinnaker/spinnaker-monitoring>`_
* orca-bootstrap
* `orca <https://github.com/spinnaker/orca>`_
* redis-bootstrap
* redis
* `rosco <https://github.com/spinnaker/rosco>`_
    * Controls the Bake Stage for creating machine images: AMIs
    * Uses Packer underneath to provision machines and run configuration
      management
* vault-client
* vault-server

----------------
Service Settings
----------------

* https://www.spinnaker.io/reference/halyard/custom/

Override Kubernetes Service Settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To override Kubernetes Service settings in the generated file
:file:`.hal/default/history/service-settings.yml`, create a file
:file:`.hal/default/service-settings/{SERVICE}.yml`.

Example :file:`.hal/default/service-settings/echo.yml`:

.. code-block:: yaml

   kubernetes:
     podAnnotations:
       sumologic.com/format: text
       sumologic.com/sourceCategory: spinnaker/echo
       sumologic.com/sourceName: echo
   env:
     JAVA_OPTS: -Xms2g -Xmx2g

Override Spring Profile Settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To override settings Spring Profile settings, create a file
:file:`.hal/default/profiles/{SERVICE}-local.yml`.

Example :file:`.hal/default/profiles/clouddriver-local.yml`:

.. code-block:: yaml

   serviceLimits:
     cloudProviderOverrides:
       aws:
         rateLimit: 15

------------
Swagger APIs
------------

Most Spinnaker Services have a Swagger UI for exploration of the API hosted at
`http://localhost:${PORT}/swagger-ui.html
<http://localhost:${PORT}/swagger-ui.html>`_. The only publicly facing Service
with Swagger is Gate. Use Kubernetes to port forward for all other private
Services.

.. code-block:: bash

   kubectl --namespace spinnaker get pods      # Find the Pod for the Spinnaker Service
   kubectl --namespace spinnaker get services  # Find the exposed port
   kubectl --namespace spinnaker port-forward ${POD_NAME} ${PORT}
   # Go to http://localhost:${PORT}/swagger-ui.html

---------------------------------
Common Services with useful APIs:
---------------------------------

* Clouddriver
* Gate
