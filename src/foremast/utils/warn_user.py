"""Overwriting the default output of warnings package."""
import warnings


def warning_format(message, category, *_, **__):
    """Warning format"""
    return '{}: {}\n'.format(category.__name__, message)

warnings.formatwarning = warning_format
warn_user = warnings.warn
