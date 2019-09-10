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


def resource_action(client, action='', log_format='item: %(key)s', **kwargs):
    """Call _action_ using boto3 _client_ with _kwargs_.

    This is meant for _action_ methods that will create or implicitely prove a
    given Resource exists. The _log_failure_ flag is available for methods that
    should always succeed, but will occasionally fail due to unknown AWS
    issues.

    Args:
        client (botocore.client.IAM): boto3 client object.
        action (str): Client method to call.
        log_format (str): Generic log message format, 'Added' or 'Found' will
            be prepended depending on the scenario.
        prefix (str): Prefix word to use in successful INFO message.
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

        if error_code == 'AccessDenied':
            LOG.fatal(error)
            raise
        elif error_code == 'EntityAlreadyExists':
            LOG.info(' '.join(('Found', log_format)), kwargs)
        else:
            LOG.fatal(error)

    return result
