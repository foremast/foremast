``services`` Block
~~~~~~~~~~~~~~~~~~

Access to different Cloud Services will be added to an inline Policy for an IAM
Role. Keys must match with a corresponding template in
:file:`src/foremast/templates/infrastructure/iam/{key}.json.j2`.

``cloudformation``
******************

Add CloudFormation access.

   | *Type*: bool
   | *Default*: ``false``

``dynamodb``
************

Add DynamoDB access to tables listed.

   | *Type*: list
   | *Default*: ``[]``

``lambda``
**********

Add Lambda access.

   | *Type*: bool
   | *Default*: ``false``

``s3``
******

Add S3 access.

   | *Type*: bool
   | *Default*: ``false``

``ses``
*******

Add SES access.

   | *Type*: bool
   | *Default*: ``false``

``sns``
*******

Add SNS access.

   | *Type*: bool
   | *Default*: ``false``

``sqs``
*******

Add SQS access.

   | *Type*: bool
   | *Default*: ``false``
