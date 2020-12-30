#   Foremast - Pipeline Tooling
#
#   Copyright 2018 Gogo, LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""Generic boto3 Resource action caller."""
import logging

from boto3.exceptions import botocore

LOG = logging.getLogger(__name__)


def resource_action(client, action='', log_format='item: %(key)s', raise_errors=False, **kwargs):
    """Call _action_ using boto3 _client_ with _kwargs_.

    This is meant for _action_ methods that will create or implicitly prove a
    given Resource exists. This method will fail silently and log errors by default,
    use the raise_errors flag to change this functionality.  AccessDenied errors will
    always cause a raised error. EntityAlreadyExists will never raise an error.

    Args:
        client (botocore.client.IAM): boto3 client object.
        action (str): Client method to call.
        log_format (str): Generic log message format, 'Added' or 'Found' will
            be prepended depending on the scenario.
        raise_errors (bool): If errors should be raised, defaults to False.
            AccessDenied errors will always cause a raised error.
            EntityAlreadyExists will never raise an error.
        **kwargs: Keyword arguments to pass to _action_ method.

    Returns:
        dict: boto3 response.
    """
    result = None

    try:
        result = getattr(client, action)(**kwargs)
        LOG.info(log_format, kwargs)
    except botocore.exceptions.ClientError as error:
        error_code = error.response['Error']['Code']

        if raise_errors or error_code in "AccessDenied":
            LOG.fatal(error)
            raise
        elif error_code == 'EntityAlreadyExists':
            LOG.info(' '.join(('Found', log_format)), kwargs)
        else:
            LOG.fatal(error)

    return result
