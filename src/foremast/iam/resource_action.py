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
        **kwargs: Keyword arguments to pass to _action_ method.

    Returns:
        True upon successful completion.
    """
    try:
        getattr(client, action)(**kwargs)
        LOG.info(' '.join(('Added', log_format)), kwargs)
    except botocore.exceptions.ClientError as error:
        error_code = error.response['Error']['Code']

        if error_code == 'AccessDenied':
            LOG.fatal(error)
            raise
        elif error_code == 'EntityAlreadyExists':
            LOG.info(' '.join(('Found', log_format)), kwargs)
        else:
            LOG.fatal(error)

    return True
