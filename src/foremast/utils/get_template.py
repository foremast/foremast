"""Render Jinja2 template."""
import logging
import os

import jinja2

LOG = logging.getLogger(__name__)


def get_template(template_file='', **kwargs):
    """Get the Jinja2 template and renders with dict _kwargs_.

    Args:
        kwargs: Keywords to use for rendering the Jinja2 template.

    Returns:
        String of rendered JSON template.
    """
    here = os.path.dirname(os.path.realpath(__file__))
    templatedir = '{0}/../templates/'.format(here)
    LOG.debug('Template directory: %s', templatedir)
    LOG.debug('Template file: %s', template_file)

    jinjaenv = jinja2.Environment(loader=jinja2.FileSystemLoader(templatedir))
    template = jinjaenv.get_template(template_file)
    for key, value in kwargs.items():
        LOG.debug('%s => %s', key, value)
    rendered_json = template.render(**kwargs)

    LOG.debug('Rendered JSON:\n%s', rendered_json)
    return rendered_json
