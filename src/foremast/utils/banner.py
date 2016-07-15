"""Prints a banner.

Example:

================================================================================
                             Create Security Group
================================================================================
"""
import logging

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)

def banner(text, border='=', width=80):
    """Center _text_ in a banner _width_ wide with _border_ characters.

    Args:
        text (str): What to write in the banner
        border (str): Border character
        width (int): How long the border should be
    """
    text_padding = '{0:^%d}' % (width)
    LOG.info(border * width)
    LOG.info(text_padding.format(text))
    LOG.info(border * width)
