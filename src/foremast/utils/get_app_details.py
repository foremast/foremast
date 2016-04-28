import murl
import requests
import collections
import googutils
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

    app_details = requests.get(api.url).json()
    assert app_details.ok, 'App does not Exist'

    group = app_details['attributes'].get('repoProjectKey')
    project = app_details['attributes'].get('repoSlug')
    generated = gogoutils.Generator(group, project, env=env)

    app_details = collections.namedtuple('AppDetails',
                                         ['group', 'policy', 'profile', 'role',
                                          'user'])
    details = app_details(**generated.iam())

    LOG.debug('Application details: %s', details)
    return details
