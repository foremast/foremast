"""Check Pipeline name to match format."""
import logging

LOG = logging.getLogger(__name__)


def check_managed_pipeline(name='', app_name=''):
    """Check a Pipeline name is a managed format **app_name [region]**.

    Args:
        name (str): Name of Pipeline to check.
        app_name (str): Name of Application to find in Pipeline name.

    Returns:
        str: Region name from managed Pipeline name.

    Raises:
        ValueError: Pipeline is not managed.
    """
    *pipeline_name_prefix, bracket_region = name.split()
    region = bracket_region.strip('[]')

    not_managed_message = '"{0}" is not managed.'.format(name)

    if not all([bracket_region.startswith('['), bracket_region.endswith(']')]):
        LOG.debug('"%s" does not end with "[region]".', name)
        raise ValueError(not_managed_message)

    if len(pipeline_name_prefix) is not 1:
        LOG.debug('"%s" does not only have one word before [region].', name)
        raise ValueError(not_managed_message)

    if app_name not in pipeline_name_prefix:
        LOG.debug('"%s" does not use "%s" before [region].', name, app_name)
        raise ValueError(not_managed_message)

    return region
