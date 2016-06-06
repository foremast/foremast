"""Prints a banner.

Example:

================================================================================
                             Create Security Group
================================================================================
"""
import logging

from foremast import consts

LOG = logging.getLogger(__name__)
logging.basicConfig(format=consts.LOGGING_FORMAT)
logging.getLogger("foremast").setLevel(logging.INFO)


def banner(text, border='=', width=80):
    """Center _text_ in a banner _width_ wide with _border_ characters."""
    text_padding = '{0:^%d}' % (width)
    LOG.info(border * width)
    LOG.info(text_padding.format(text))
    LOG.info(border * width)
