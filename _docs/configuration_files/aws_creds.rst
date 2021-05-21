.. _aws_creds:

===============
AWS Credentials
===============

.. contents::
   :local:

Purpose
-------

This is how AWS credentials are stored for usage with Foremast. All AWS calls
outside of Spinnaker use Boto3 so standard Boto3 locations work but
account/environment must be specified.

Example Configuration
---------------------

.. code-block:: ini

    [build]
    aws_access_key_id = XXXXXXXXXXXXXXXXXXXXXXXXXX
    aws_secret_access_key = yyyyyyyxxxxxxxxyyyyyyyyyyyyyxxxxxxx

    [dev]
    aws_access_key_id = AAAAAAAAAAAAAAAAAAAAAAAAAA
    aws_secret_access_key = bbbbbbbbbaaaaaaaaaaaabbbbbbbbbbaaaaa

    [stage]
    aws_access_key_id = TTTTTTTTTTTTTTTTTTTTTTTTTT
    aws_secret_access_key = sssssssssssstttttttttttttttsssssssss


Configuration Location
----------------------

Foremast just uses Boto3 which will look at ``~/.aws/credentials`` for the
``credentials`` file.

Configuration Details
---------------------

This is a standard Boto3 ``credentials`` file. You can read more about it on the
`Boto3 docs <http://boto3.readthedocs.io/en/latest/guide/configuration.html>`_.
The important part is that each account/environment that Foremast is managing
has a distinct section in ``credentials``.
