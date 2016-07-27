"""Retrieve Application details."""
import logging

import gogoutils
import murl
import requests

from ..consts import API_URL, APP_FORMATS
from ..exceptions import SpinnakerAppNotFound

LOG = logging.getLogger(__name__)


def get_details(app='groupproject', env='dev'):
    """Extract details for Application.

    Args:
        app (str): Application Name
        env (str): Environment/account to get details from

    Returns:
        collections.namedtuple with _group_, _policy_, _profile_, _role_,
            _user_.
    """
    api = murl.Url(API_URL)
    api.path = 'applications/{app}'.format(app=app)

    request = requests.get(api.url)

    if not request.ok:
        raise SpinnakerAppNotFound('"{0}" not found.'.format(app))

    app_details = request.json()

    LOG.debug('App details: %s', app_details)
    group = app_details['attributes'].get('repoProjectKey')
    project = app_details['attributes'].get('repoSlug')
    generated = gogoutils.Generator(group, project, env=env,
                                    formats=APP_FORMATS)

    LOG.debug('Application details: %s', generated)
    return generated
