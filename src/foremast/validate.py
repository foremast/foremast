"""Spinnaker validate functions."""
import logging

from .consts import API_URL
from .utils.credentials import get_env_credential

LOG = logging.getLogger(__name__)


def validate_gate():
    """Check Gate connection."""
    try:
        credentials = get_env_credential()
        LOG.debug('Found credentials: %s', credentials)
        LOG.info('Gate working.')
    except TypeError:
        LOG.fatal('Gate connection not valid: API_URL = %s', API_URL)


def validate_all(args):
    """Run all validate steps."""
    LOG.debug('Args: %s', args)

    LOG.info('Running all validate steps.')
    validate_gate()
