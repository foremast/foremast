"""Prints a banner.
 
Example:
 
================================================================================
                              Create Security Group
================================================================================
"""
 
 
def banner(text, border='=', width=80):
    """Center _text_ in a banner _width_ wide with _border_ characters."""
    text_padding = '{0:^%d}' % (width)
    print(border * width)
    print(text_padding.format(text))
    print(border * width)
