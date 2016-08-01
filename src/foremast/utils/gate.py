#   Foremast - Pipeline Tooling
#
#   Copyright 2016 Gogo, LLC
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

"""Dynamic Gate API interface.

It is best to use a new Class Instance for each request unless something is
keeping close track of _self.path_. Reusing an Instance will have adverse
affects as _self.path_ will not be cleared automatically.

Examples:
    Typical imports::

        from foremast.utils import Gate
        from .utils import Gate

    Responses will be a *dict* type::

        response = Gate().credentials.dev.get()
        response = Gate('credentials/dev').get()
        type(response) == dict

    The first arguments is expected to be a JSON *str* or *dict* representation
    and will be passed to the **json** argument of the _requests_ call::

        response = Gate().tasks.post({'json': 'data'})
        # requests.post(json={'json': 'data'})

    Keyword arguments besides _json_dict_ will be passed to **data** or
    **params** of the _requests_ call::

        response = Gate().tasks.post({'json': 'data'}, custom='param')
        # requests.post(json={'json': 'data'}, data={'custom': 'param'})

    What is happening? The normal instantiation initializes the request path to
    an empty string::

        a = Gate()
        a.path == ''

    Accessing attributes will append the accessed attribute to the end of the
    path::

        b = Gate().applications
        # __getattr__() appends 'applications' to self.path and returns self
        b.path == '/applications'

    This continues recursively because each attribute access will return a
    reference to the current Instance::

        c = Gate().applications.coreforrest
        # __getattr__() appends 'applications' to self.path and returns self
        # __getattr__() appends 'coreforrest' to self.path and returns self
        c.path == '/applications/coreforrest'

    Once an HTTP method matches, the Instance's **verb** attribute will be set
    in preparation for the _requests_ call::

        d = Gate().applications.coreforrest.get
        # __getattr__() appends 'applications' to self.path and returns self
        # __getattr__() appends 'coreforrest' to self.path and returns self
        # __getattr__() sets 'get' to self.verb and returns self
        d.path == '/applications/coreforrest'
        d.verb == 'get'

    Finally ending with *()* will trigger the _requests_ call. The following are
    all equivalent calls based on the previous examples::

        d() == c.get()
        d() == b.coreforrest.get()
        d() == a.applications.coreforrest.get()
        d() == Gate().applications.coreforrest.get()
        # __getattr__() appends 'applications' to self.path and returns self
        # __getattr__() appends 'coreforrest' to self.path and returns self
        # __getattr__() sets 'get' to self.verb and returns self
        # __call__() executes the request
        # requests.get() is used because d.verb == 'get'
        # requests.get(API_URL + '/applications/coreforrest')

    Reusing an Instance is discouraged due to stored Instance attributes::

        e = Gate().applications
        e.coreforrest.get()
        # Succeeds because e.path == '/applications/coreforest'
        e.edgeforrest.get()
        # Fails because e.path == '/applications/coreforrest/edgeforrest'
"""
import json
import logging

import murl
import requests

from ..consts import API_URL, HEADERS

LOG = logging.getLogger(__name__)


class Gate(object):
    """Dynamic Gate API interface.

    Args:
        path (str): URL path or full URL.
    """

    def __init__(self, path=''):
        self.path = path
        self.verb = ''

    def __getattr__(self, attr):
        """Use attributes to construct URL path for request.

        Args:
            attr (str): URL path directory segment, e.g. applications, tasks.
        """
        LOG.debug('attr=%s', attr)

        attr_lower = attr.lower()
        if attr_lower in set(['delete', 'get', 'patch', 'post', 'put']):
            self.verb = attr_lower
        else:
            self.path = '/'.join([self.path, attr])

        return self

    def __call__(self, json_data='', **kwargs):
        """Issue request to Gate API.

        Args:
            json_data (str): JSON content to send in request.
            path (str): URL path to reqest from Gate API.

        Returns:
            dict: JSON response body returned by Gate API.

        Raises:
            AssertionError: Gate API did not return a 200 status code.
        """
        LOG.debug('json_data=%(json_data)s\nkwargs=%(kwargs)s', locals())

        url = self.normalize_url()
        request_kwargs = self.assemble_request_kwargs(json_data, kwargs)

        response = getattr(requests, self.verb)(url.url, **request_kwargs)

        assert response.ok, 'Gate API {0} request to {1} failed: {2}'.format(
            self.verb.upper(), self.path, response.text)

        LOG.debug('Gate response: %s', response.text)

        if not response.text:
            response_dict = {}
        else:
            try:
                response_dict = response.json()
            except json.decoder.JSONDecodeError:
                response_dict = {}
        LOG.debug('Gate API response: %s', response_dict)
        return response_dict

    def assemble_request_kwargs(self, json_data, kwargs):
        """Construct kwargs for final request.

        Args:
            json_data (str): JSON content to send in request.
            path (str): URL path to reqest from Gate API.

        Returns:
            dict: Assembled kwargs::

                {
                    'headers': {'accept': '*/*', ...},
                    'data': {'extra': 'arguments', ...},
                    'json': {'name': 'coreforrest', ...}
                }
        """
        request_kwargs = {'headers': HEADERS}

        if self.verb in set(['get']):
            request_kwargs.update({'params': kwargs})
        elif self.verb in set(['patch', 'post', 'put']):
            try:
                request_json = json.loads(json_data)
            except (json.decoder.JSONDecodeError, TypeError):
                request_json = json_data

            request_kwargs.update({'json': request_json, 'data': kwargs})

        LOG.debug('Request kwargs: %s', request_kwargs)
        return request_kwargs

    def normalize_url(self):
        """Return URL based on _self.path_ or construct from _API_URL_."""
        url = murl.Url(self.path)
        if not url.scheme:
            url = murl.Url(API_URL)
            url.path = self.path
        LOG.debug('Request URL: %s', url.url)
        return url
