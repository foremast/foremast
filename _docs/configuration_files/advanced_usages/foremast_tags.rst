.. _foremast_tags

########
AWS Tags
########

This section addresses features that can be enabled/disabled by specific tags by AWS resources.

AWS S3 Bucket Tags
******************

Foremast can leverage S3 bucket tags to allow/restrict specific Foremast features.

``FOREMAST_LAMBDA_RESTRICT_BUCKET_NOTIFICATIONS``
=================================================

  Restricts Foremast Lambda Deployment Triggers from overriding S3 bucket triggers

      | *Type*: string
      | *Required*: False
      | *Example*: ``"true"`` ``"false"``