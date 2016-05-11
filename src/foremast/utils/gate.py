"""Dynamic Gate API interface.

Examples:
    Gate().credentials.dev.get()
    Gate('credentials/dev').get()
    Gate().tasks.post({'all': 'data'})
"""
import json
import functools
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
        LOG.debug('path: %s', self.path)

    def __getattr__(self, attr):
        """Use attributes to construct URL path for request.

        Args:
            attr (str): URL path directory segment, e.g. applications, tasks.
        """
        LOG.debug('attr=%(attr)s\nkwargs=%(kwargs)s', locals())

        if attr.lower() in ('delete', 'get', 'patch', 'post', 'put'):
            return functools.partial(self, verb=attr)

        return Gate(path='/'.join([self.path, attr]))

    def __call__(self, json_data='', verb='get', **kwargs):
        """Issue request to Gate API.

        Args:
            json_data (str): JSON content to send in request.
            path (str): URL path to reqest from Gate API.
            verb (str): HTTP verb to use, e.g. delete, get, patch, post, put.

        Returns:
            dict: JSON response body returned by Gate API.

        Raises:
            AssertionError: Gate API did not return a 200 status code.
        """
        LOG.debug('json_data=%(json_data)s\n'
                  'verb=%(verb)s\n'
                  'kwargs=%(kwargs)s', locals())

        verb = verb.lower()
        url = self.normalize_url()
        request_kwargs = self.assemble_request_kwargs(json_data, kwargs, verb)

        response = getattr(requests, verb)(url.url, **request_kwargs)

        assert response.ok, 'Gate API {0} request to {1} failed: {2}'.format(
            verb.upper(), self.path, response.text)

        try:
            response_dict = response.json()
        except json.decoder.JSONDecodeError:
            response_dict = {}
        LOG.debug('Gate API response: %s', response_dict)
        return response_dict

    def assemble_request_kwargs(self, json_data, kwargs, verb):
        """Construct kwargs for final request.

        Args:
            json_data (str): JSON content to send in request.
            path (str): URL path to reqest from Gate API.
            verb (str): HTTP verb to use, e.g. delete, get, patch, post, put.

        Returns:
            dict: Assembled kwargs.

                {
                    'headers': {'accept': '*/*', ...},
                    'data': {'extra': 'arguments', ...},
                    'json': {'name': 'coreforrest', ...}
                }
        """
        request_kwargs = {'headers': HEADERS}

        if verb in set(['get']):
            request_kwargs.update({'params': kwargs})
        elif verb in set(['patch', 'post', 'put']):
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
