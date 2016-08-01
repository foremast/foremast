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
        """Recursively retrieve value for _key_ in dict.

        Args:
            key (str): dict key to get all items for
        """
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
