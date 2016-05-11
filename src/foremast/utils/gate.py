"""Dynamic Gate API interface.

Examples:
    Gate().credentials.dev.get()
    Gate('credentials/dev').get()
    Gate().tasks.post({'all': 'data'})
"""
import json
import logging

import murl
import requests

from ..consts import API_URL, HEADERS

LOG = logging.getLogger(__name__)


class Gate(object):
    """Dynamic Gate API interface."""

    def __init__(self, path=''):
        """Gate API object.

        Args:
            path (str): URL path or full URL.
        """
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
            dict: Assembled kwargs.

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
