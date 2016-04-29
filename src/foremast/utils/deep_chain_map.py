"""ChainMap modification to handle nested dict objects."""
import collections


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
        """Recursively retrieve value for _key_ in dict."""
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
