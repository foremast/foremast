"""Read properties file"""
import json


def get_properties(properties_file='', env=''):
    """Get contents of _properties_file_ for the _env_."""
    with open(properties_file, 'rt') as file_handle:
        properties = json.load(file_handle)
    return properties[env]
