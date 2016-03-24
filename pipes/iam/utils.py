import collections
import logging
import os

import murl
import requests
from jinja2 import Environment, FileSystemLoader

import gogoutils

from .consts import API_URL

LOG = logging.getLogger(__name__)


def get_details(app='groupproject', env='dev'):
    """Extract details for Application.

    Returns:
        collections.namedtuple with _group_, _policy_, _profile_, _role_,
            _user_.
    """
    api = murl.Url(API_URL)
    api.path = 'applications/{app}'.format(app=app)

    app_details = requests.get(api.url).json()

    group, project = gogoutils.Parser(app_details['attributes'][
        'repoProjectKey']).parse_url()
    generated = gogoutils.Generator(group, project, env=env)

    app_details = collections.namedtuple('AppDetails',
                                         ['group', 'policy', 'profile', 'role',
                                          'user'])
    details = app_details(**generated.iam())

    LOG.debug('Application details: %s', details)
    return details


def get_template(template_file='', **kwargs):
    """Gets the Jinja2 template and renders with dict _kwargs_.

    Args:
        kwargs: Keywords to use for rendering the Jinja2 template.

    Returns:
        String of rendered JSON template.
    """
    templatedir = os.path.sep.join((os.path.dirname(__file__), os.path.pardir,
                                    os.path.pardir, 'templates'))
    jinjaenv = Environment(loader=FileSystemLoader(templatedir))
    template = jinjaenv.get_template(template_file)
    rendered_json = template.render(**kwargs)

    LOG.debug('Rendered JSON:\n%s', rendered_json)
    return rendered_json
