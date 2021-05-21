========
Problems
========

Issues that have come up when deploying or managing Spinnaker.

.. contents::

----------
Kubernetes
----------

Pods in Unknown State
^^^^^^^^^^^^^^^^^^^^^

* Seems to happen when :command:`hal deploy apply` gives up after waiting on
  the bootstrap Services
* Not able to delete Pods
* Have to restart Docker Daemon on Nodes, or rotate Nodes out
* Solution:
   * Seems like this does not occur when running on Kubernetes Nodes
     with more resources available

----
Fiat
----

Fiat does not come up
^^^^^^^^^^^^^^^^^^^^^

* Shows error

   .. code-block:: java

      2018-08-09 08:39:51.952 ERROR 1 --- [ecutionAction-6] c.n.s.fiat.roles.UserRolesSyncer         : [] Unable to resolve service account permissions.
      com.netflix.spinnaker.fiat.permissions.PermissionResolutionException: com.netflix.spinnaker.fiat.providers.ProviderException: (Provider: DefaultAccountProvider) retrofit.RetrofitError: connect timed out

* Solution:
   * Make sure Clouddriver has a Pod running
   * https://github.com/spinnaker/fiat/blob/397706a98b56d4470a06f63972048a3157f98aaf/fiat-roles/src/main/java/com/netflix/spinnaker/fiat/providers/internal/ClouddriverService.java#L32-L36
   * Make sure ``spec.replicas`` > 0

      .. code-block:: bash

         kubectl -n spinnaker get pods
         kubectl -n spinnaker get replicasets
         kubectl -n spinnaker edit replicasets spin-clouddriver-v###

------------
Gate API SSL
------------

Gate not serving x.509 port
^^^^^^^^^^^^^^^^^^^^^^^^^^^

* x.509 port defined as ``default.apiPort: 8085`` in :file:`gate-local.yml`
* Output of :command:`netstat -ntlp` on Gate shows no listener on 8085
* Solution:
   * Requires SSL to be enabled

      .. code-block:: bash

         hal config security api ssl enable

Using a self-signed Certificate for Gate with Traefik Ingress controller
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* :command:`hal config security api ssl enable`
* Loading page shows ``502 Bad Gateway``
* Traefik Ingress using HTTP to communicate with the new HTTPS port
* Traefik recognizes the scheme based on port, if 443 use HTTPS
* Solution:
   * Configure Traefik to use HTTPS
   * Update Gate Service with :command:`kubectl` to route port 443

      .. code-block:: yaml

         apiVersion: v1
         kind: Service
         metadata:
           name: spin-gate
           namespace: spinnaker
           annotations:
             prometheus.io/path: /prometheus_metrics
             prometheus.io/port: "8008"
             prometheus.io/scrape: "true"
         spec:
           ports:
           - name: https
             port: 443
             targetPort: 8084
           - name: http
             port: 8084
             targetPort: 8084

   * Update Gate Ingress to use Service port 443

      .. code-block:: yaml

         apiVersion: extensions/v1beta1
         kind: Ingress
         metadata:
           name: spin-gate
           namespace: spinnaker
         spec:
           rules:
             - host: gate.example.com
               http:
                 paths:
                   - path: /
                     backend:
                       serviceName: spin-gate
                       servicePort: https

   * Now page loads with ``500 Internal Server Error``

Loading page shows ``500 Internal Server Error``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Traefik Ingress does not trust self-signed Certificate
* Possible solutions:
   * Use a publicly trusted Certificate
   * Add the private Certificate Authority to Traefik
   * Set ``insecuritySkipVerify = true`` in Traefik's global
     configuration
* Solution:
   * Short term, set ``insecureSkipVerify = true``
   * Add configuration file for Traefik

      .. code-block:: yaml

         apiVersion: v1
         kind: ConfigMap
         metadata:
           name: traefik-config
           namespace: kube-system
         data:
           traefik.toml: |
             logLevel = "INFO"

             insecureSkipVerify = true

   * Mount Traefik configuration file

      .. code-block:: yaml

         kind: Deployment
         apiVersion: extensions/v1beta1
         metadata:
           name: traefik-ingress-controller
           namespace: kube-system
           labels:
             k8s-app: traefik-ingress-lb
         spec:
           template:
             spec:
               containers:
               - image: traefik
                 name: traefik-ingress-lb
                 args:
                 - --api
                 - --kubernetes
                 volumeMounts:
                 - name: traefik-config
                   mountPath: /etc/traefik
               volumes:
               - name: traefik-config
                 configMap:
                   name: traefik-config

   * Page now loads as expected

Creating an Application will result in an ``Access denied`` error
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Front50 returns 403 (permission denied)
* Orca error in logs:

   .. code-block:: java

      2018-05-29 14:14:59.937 ERROR 1 --- [    handlers-19] c.n.s.orca.q.handler.RunTaskHandler      : [] Error running UpsertApplicationTask for orchestration[00000000-0000-0000-0000-000000000000]
      retrofit.RetrofitError: 403
          at retrofit.RetrofitError.httpError(RetrofitError.java:40)
          at retrofit.RestAdapter$RestHandler.invokeRequest(RestAdapter.java:388)
          at retrofit.RestAdapter$RestHandler.invoke(RestAdapter.java:240)
          at com.sun.proxy.$Proxy106.get(Unknown Source)
          at com.netflix.spinnaker.orca.front50.Front50Service$get.call(Unknown Source)
          at com.netflix.spinnaker.orca.front50.tasks.AbstractFront50Task.fetchApplication(AbstractFront50Task.groovy:73)
          at com.netflix.spinnaker.orca.applications.tasks.UpsertApplicationTask.performRequest(UpsertApplicationTask.groovy:39)
          at com.netflix.spinnaker.orca.applications.tasks.UpsertApplicationTask$performRequest.callCurrent(Unknown Source)
          at com.netflix.spinnaker.orca.front50.tasks.AbstractFront50Task.execute(AbstractFront50Task.groovy:67)
          at com.netflix.spinnaker.orca.q.handler.RunTaskHandler$handle$1$1.invoke(RunTaskHandler.kt:82)
          at com.netflix.spinnaker.orca.q.handler.RunTaskHandler$handle$1$1.invoke(RunTaskHandler.kt:51)
          at com.netflix.spinnaker.orca.q.handler.AuthenticationAwareKt$sam$Callable$55f02348.call(AuthenticationAware.kt)
          at com.netflix.spinnaker.security.AuthenticatedRequest.lambda$propagate$1(AuthenticatedRequest.java:79)
          at com.netflix.spinnaker.orca.q.handler.AuthenticationAware$DefaultImpls.withAuth(AuthenticationAware.kt:49)
          at com.netflix.spinnaker.orca.q.handler.RunTaskHandler.withAuth(RunTaskHandler.kt:51)
          at com.netflix.spinnaker.orca.q.handler.RunTaskHandler$handle$1.invoke(RunTaskHandler.kt:81)
          at com.netflix.spinnaker.orca.q.handler.RunTaskHandler$handle$1.invoke(RunTaskHandler.kt:51)
          at com.netflix.spinnaker.orca.q.handler.RunTaskHandler$withTask$1.invoke(RunTaskHandler.kt:173)
          at com.netflix.spinnaker.orca.q.handler.RunTaskHandler$withTask$1.invoke(RunTaskHandler.kt:51)
          at com.netflix.spinnaker.orca.q.handler.OrcaMessageHandler$withTask$1.invoke(OrcaMessageHandler.kt:47)
          at com.netflix.spinnaker.orca.q.handler.OrcaMessageHandler$withTask$1.invoke(OrcaMessageHandler.kt:31)
          at com.netflix.spinnaker.orca.q.handler.OrcaMessageHandler$withStage$1.invoke(OrcaMessageHandler.kt:57)
          at com.netflix.spinnaker.orca.q.handler.OrcaMessageHandler$withStage$1.invoke(OrcaMessageHandler.kt:31)
          at com.netflix.spinnaker.orca.q.handler.OrcaMessageHandler$DefaultImpls.withExecution(OrcaMessageHandler.kt:66)
          at com.netflix.spinnaker.orca.q.handler.RunTaskHandler.withExecution(RunTaskHandler.kt:51)
          at com.netflix.spinnaker.orca.q.handler.OrcaMessageHandler$DefaultImpls.withStage(OrcaMessageHandler.kt:53)
          at com.netflix.spinnaker.orca.q.handler.RunTaskHandler.withStage(RunTaskHandler.kt:51)
          at com.netflix.spinnaker.orca.q.handler.OrcaMessageHandler$DefaultImpls.withTask(OrcaMessageHandler.kt:40)
          at com.netflix.spinnaker.orca.q.handler.RunTaskHandler.withTask(RunTaskHandler.kt:51)
          at com.netflix.spinnaker.orca.q.handler.RunTaskHandler.withTask(RunTaskHandler.kt:166)
          at com.netflix.spinnaker.orca.q.handler.RunTaskHandler.handle(RunTaskHandler.kt:63)
          at com.netflix.spinnaker.orca.q.handler.RunTaskHandler.handle(RunTaskHandler.kt:51)
          at com.netflix.spinnaker.q.MessageHandler$DefaultImpls.invoke(MessageHandler.kt:36)
          at com.netflix.spinnaker.orca.q.handler.OrcaMessageHandler$DefaultImpls.invoke(OrcaMessageHandler.kt)
          at com.netflix.spinnaker.orca.q.handler.RunTaskHandler.invoke(RunTaskHandler.kt:51)
          at com.netflix.spinnaker.orca.q.audit.ExecutionTrackingMessageHandlerPostProcessor$ExecutionTrackingMessageHandlerProxy.invoke(ExecutionTrackingMessageHandlerPostProcessor.kt:47)
          at com.netflix.spinnaker.q.QueueProcessor$pollOnce$1$1.run(QueueProcessor.kt:74)
          at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
          at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
          at java.lang.Thread.run(Thread.java:748)

* Solution:
   * Set ``fiat.cache.expiresAfterWriteSeconds: 0`` in :file:`fiat-local.yml`
     and ``services.fiat.cache.expiresAfterWriteSeconds: 0`` in
     :file:`spinnaker-local.yml`

      * https://www.bountysource.com/issues/48656889-application-not-found-and-delay-issue-in-ui
      * Property needs to be set in both files
      * Reduces the default 20 seconds
   * Application creation workflow now goes:
      * Front50 responds 404 (not found) instead of 403 (access denied)

         .. code-block:: java

            com.netflix.spinnaker.front50.exception.NotFoundException: Object not found (key: exampleapplication)

      * Create Application
      * Application exists immediately

-------------
Authorization
-------------

Disable Clusters
^^^^^^^^^^^^^^^^

* Anyone is able to disable and enable Clusters
* Destroying a Cluster will disable the Cluster, then fail when destroying
  with error ``Access denied to account ${ACCOUNT}``
* Solution:
   * Will fail properly with Traffic Guards enabled for Cluster

Traffic Guards
^^^^^^^^^^^^^^

* Anyone can modify the Traffic Guards for an Application
* After removing safety, someone can later disable a Cluster and take down
  traffic

----------------------
Provider Rate Limiting
----------------------

AWS throttling errors
^^^^^^^^^^^^^^^^^^^^^

* ``ThrottleException`` in Clouddriver logs

   .. code-block:: java

      2018-05-09 01:36:48.681  INFO 1 --- [cutionAction-47] com.amazonaws.latency                    : ServiceName=[AmazonElasticLoadBalancing], ThrottleException=[com.amazonaws.services.elasticloadbalancingv2.model.AmazonElasticLoadBalancingException: Rate exceeded (Service: AmazonElasticLoadBalancing; Status Code: 400; Error Code: Throttling; Request ID: 00000000-0000-0000-0000-000000000000)], AWSErrorCode=[Throttling], StatusCode=[400, 200], ServiceEndpoint=[https://elasticloadbalancing.us-west-2.amazonaws.com], RequestType=[DescribeTargetHealthRequest], AWSRequestID=[00000000-0000-0000-0000-000000000000, 00000000-0000-0000-0000-000000000000], HttpClientPoolPendingCount=0, RetryCapacityConsumed=0, ThrottleException=1, HttpClientPoolAvailableCount=0, RequestCount=2, HttpClientPoolLeasedCount=0, RetryPauseTime=[474.151], RequestMarshallTime=[0.002], ResponseProcessingTime=[0.214], ClientExecuteTime=[700.076], HttpClientSendRequestTime=[0.059, 0.048], HttpRequestTime=[4.672, 42.883], RequestSigningTime=[0.082, 0.105], CredentialsRequestTime=[0.002, 0.002, 0.003], HttpClientReceiveResponseTime=[4.564, 27.471],

* Solution:
   * Decrease allowed Provider API requests per second
      * https://github.com/spinnaker/clouddriver/pull/1291
      * https://blog.armory.io/fine-grained-rate-limits-for-spinnaker-clouddriver/

----------------------
Application Deployment
----------------------

Error when deploying an Application
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: none

   Exception ( Monitor Deploy )
   unable to resolve AMI imageId from ami-a5532fdd

* Solution:
   * Fix where Clouddriver is trying to find AMIs
   * Not sure what the :command:`hal` command is, but modify :file:`.hal/config`
     so ``primaryAccount`` is the Account to search

      .. code-block:: yaml

         deploymentConfigurations:
         - name: default
           providers:
             aws:
               primaryAccount: HALYARD_AWS_ACCOUNT_NAME

Exception ( Determine Source Server Group ) 403
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: none

   Exception ( Determine Source Server Group )
   403

* Solution 1:
   * Missing ``READ`` permissions for Account
   * Look at :file:`.hal/config` for what Roles are listed under ``READ``
   * For Service Accounts, add the Role
   * For Users, add the User to the Group in the SAML or other authentication
     Provider
* Solution 2:
   * Deploy Stage ``application`` value does not match Spinnaker Application
   * In the UI, the ``Cluster`` name should be the same as the Spinnaker
     Application

----------------
Pipeline Trigger
----------------

Pipelines not triggering when Fiat enabled
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: none

   # Igor
   2018-10-25 23:25:06.607  INFO 1 --- [RxIoScheduler-4] c.n.s.igor.jenkins.JenkinsBuildMonitor   : [master=Jenkins:job=example-job] has no other builds between [Thu Oct 25 23:21:42 GMT 2018 - Thu Oct 25 23:24:00 GMT 2018], advancing cursor to 1540509840709

   # Echo
   2018-10-25 23:25:06.607  INFO 1 --- [IoScheduler-987] c.n.s.e.p.monitor.TriggerMonitor         : Found matching pipeline example-application:example-pipeline
   2018-10-25 23:25:06.607  INFO 1 --- [IoScheduler-987] c.n.s.e.p.orca.PipelineInitiator         : Triggering Pipeline(example-application, example-pipeline, 00000000-0000-0000-0000-000000000000) due to Trigger(00000000-0000-0000-0000-000000000000, jenkins, Jenkins, example-job, null, gitlab, null, null, null, null, null, null, {}, null, {}, null, null, [], null, null, null, null, Pipeline(example-application, example-pipeline, 00000000-0000-0000-0000-000000000000))
   2018-10-25 23:25:06.608  INFO 1 --- [it-/orchestrate] c.n.s.e.p.orca.OrcaService               : ---> HTTP POST http://spin-orca.spinnaker:8083/orchestrate
   2018-10-25 23:25:06.651  INFO 1 --- [it-/orchestrate] c.n.s.e.p.orca.OrcaService               : <--- HTTP 403 http://spin-orca.spinnaker:8083/orchestrate (45ms)
   2018-10-25 23:25:06.693 ERROR 1 --- [  Retrofit-Idle] c.n.s.e.p.orca.PipelineInitiator         : Retrying pipeline trigger, attempt 1/5
   2018-10-25 23:25:27.023 ERROR 1 --- [  Retrofit-Idle] c.n.s.e.p.orca.PipelineInitiator         : Error triggering pipeline: Pipeline(example-application, example-pipeline, 00000000-0000-0000-0000-000000000000)

   # Orca
   2018-10-25 23:25:06.686  INFO 1 --- [0.0-8083-exec-8] c.n.s.o.c.OperationsController           : [] received pipeline 00000000-0000-0000-0000-000000000000:{…}
   2018-10-25 23:25:06.687  INFO 1 --- [0.0-8083-exec-8] c.n.s.o.c.OperationsController           : [] requested pipeline: {…}
   2018-10-25 23:25:06.687  INFO 1 --- [0.0-8083-exec-8] c.n.s.orca.front50.Front50Service        : [] ---> HTTP GET http://spin-front50.spinnaker:8080/pipelines/example-application?refresh=false
   2018-10-25 23:25:06.692  INFO 1 --- [0.0-8083-exec-8] c.n.s.orca.front50.Front50Service        : [] <--- HTTP 403 http://spin-front50.spinnaker:8080/pipelines/example-application?refresh=false (5ms)

* Solution:
   * Missing ``Run As User`` with Application ``READ`` and ``WRITE`` Permissions
   * When not populated, the ``Run As User`` defaults to ``Anonymous``
   * When there are any Roles configured in the Application Permissions,
     ``Anonymous`` authorization no longer works
   * Create a Service Account:
     https://www.spinnaker.io/setup/security/authorization/service-accounts/
   * Configure Spinnaker Application Permissions to allow ``READ`` and ``WRITE``
     for any Role the Service Account belongs to

------------
Memory Usage
------------

Microservices will grow and consume gratuitous amounts of RAM
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Solution:
   * Set memory limits for Containers
      * https://www.spinnaker.io/reference/halyard/component-sizing/
      * Set Pod memory requests and limits in :file:`.hal/config`

         .. code-block:: yaml

            deploymentConfigurations:
            - name: default
              deploymentEnvironment:
                customSizing:
                  spin-clouddriver:
                    limits:
                      memory: 2Gi

   * Set the JVM flags to be 80-90%
     :file:`.hal/default/service-settings/clouddriver.yml`

      .. code-block:: yaml

         env:
           # 2GB * .8
           JAVA_OPTS: -Xmx1638m

   * ``-Xms`` should be 80-90% of Pod ``requests``
   * ``-Xmx`` should be 80-90% of Pod ``limits``

------
Web UI
------

Availability Zones do not show when creating a Load Balancer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* JavaScript Console errors when selecting Account

   .. code-block:: js

      TypeError: Cannot read property 'slice' of undefined

* Solution:
   * Specify default Account and Region in Deck
   * Use :file:`.hal/default/profiles/settings-local.js` to override the defaults
     in :file:`.hal/default/staging/settings.js`

      .. code-block:: js

         window.spinnakerSettings.providers.aws.defaults = {
             account: 'test',
             region: 'us-east-5',
             iamRole: 'DEFAULT_IAM_PROFILE',
         };

``Create an internal load balancer`` not checked by default
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Have to remember to check `Create an internal load balancer` when creating
  Load Balancers
* Solution:
   * Configure Deck to infer the Internal flag based on the Subnet Purpose name
   * Use :file:`.hal/default/profiles/settings-local.js` to override the defaults
     in :file:`.hal/default/staging/settings.js`

      .. code-block:: js

         window.spinnakerSettings.providers.aws.loadBalancers.inferInternalFlagFromSubnet = true;
