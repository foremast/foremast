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
