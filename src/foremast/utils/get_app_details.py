import murl
import requests
import collections
import gogoutils
import logging

from ..consts import API_URL

LOG = logging.getLogger(__name__)


def get_details(app='groupproject', env='dev'):
    """Extract details for Application.

    Returns:
        collections.namedtuple with _group_, _policy_, _profile_, _role_,
            _user_.
    """
    api = murl.Url(API_URL)
    api.path = 'applications/{app}'.format(app=app)

    request = requests.get(api.url)
    assert request.ok, 'App does not Exist'

    app_details = request.json()

    LOG.debug('App details: %s', app_details)
    group = app_details['attributes'].get('repoProjectKey')
    project = app_details['attributes'].get('repoSlug')
    generated = gogoutils.Generator(group, project, env=env)

    LOG.debug('Application details: %s', generated)
    return generated
