import collections
import configparser
import logging
import os

import jinja2

LOG = logging.getLogger(__name__)


class DeepChainMap(collections.ChainMap):
    """Deep lookups for collections.ChainMap objects.

    When there are nested dicts, the first found, second level dict is returned
    instead of overlaying alternative second level dicts.

        >>> first = {'key1': {'key1_1': 'first_one'}}
        >>> second = {'key1': {'key1_1': 'second_one', 'key1_2': 'second_two'}}
        >>> collections.ChainMap(first, second)['key1']
        {'key1_1': 'first_one'}
        >>> collections.ChainMap(second, first)['key1']
        {'key1_1': 'second_one', 'key1_2': 'second_two'}

        # Deep lookup will flatten every level.

        >>> DeepChainMap(first, second)['key1']
        {'key1_1': 'first_one', 'key1_2': 'second_two'}
        >>> DeepChainMap(second, first)['key1']
        {'key1_1': 'second_one', 'key1_2': 'second_two'}
    """

    def __getitem__(self, key):
        for mapping in self.maps:
            try:
                value = mapping[key]
                if isinstance(value, dict):
                    return dict(DeepChainMap(*list(mapping.get(key, {})
                                                   for mapping in self.maps)))
                else:
                    return value
            except KeyError:
                pass
        return self.__missing__(key)


def get_configs(file_name='spinnaker.conf'):
    """Get main configuration.

    Args:
        file_name (str): Name of configuration file to retrieve.

    Returns:
        configparser.ConfigParser object with configuration loaded.
    """
    here = os.path.dirname(os.path.realpath(__file__))
    configpath = '{0}/../../configs/{1}'.format(here, file_name)
    config = configparser.ConfigParser()
    config.read(configpath)

    LOG.debug('Configuration sections found: %s', config.sections())
    return config


def get_template(template_file='', **kwargs):
    """Gets the Jinja2 template and renders with dict _kwargs_.

    Args:
        kwargs: Keywords to use for rendering the Jinja2 template.

    Returns:
        String of rendered JSON template.
    """
    templatedir = os.path.sep.join((os.path.dirname(__file__), os.path.pardir,
                                    os.path.pardir, 'templates'))
    jinjaenv = jinja2.Environment(loader=jinja2.FileSystemLoader(templatedir))
    template = jinjaenv.get_template(template_file)
    rendered_json = template.render(**kwargs)

    LOG.debug('Rendered JSON:\n%s', rendered_json)
    return rendered_json
