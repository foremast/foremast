"""Spinnaker tester functions."""
import logging

from .consts import API_URL
from .utils.credentials import get_env_credential

LOG = logging.getLogger(__name__)


def gate_tester():
    """Check Gate connection."""
    try:
        credentials = get_env_credential()
        LOG.debug('Found credentials: %s', credentials)
        LOG.info('Gate working.')
    except TypeError:
        LOG.fatal('Gate connection not valid: API_URL = %s', API_URL)


def all_testers(args):
    """Run all tests.

    Args:
        args (CliArgs): Arguments from CLI.
    """
    LOG.info('Running all tests.')
    gate_tester()
