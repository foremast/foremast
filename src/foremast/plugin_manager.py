"""Manager to handle plugins"""
import pathlib

from pluginbase import PluginBase


class PluginManager:
    """Class to manage and create Spinnaker applications

    Args:
        paths (str): Path of plugin directory.
        provider (str): The name of the cloud provider.
    """

    def __init__(self, paths, provider):
        path = pathlib.Path(__file__).parent.resolve()
        path = path / paths

        all_paths = [str(path)]

        self.paths = all_paths
        self.provider = provider

        plugin_base = PluginBase(package='foremast.plugins')
        self.plugin_source = plugin_base.make_plugin_source(searchpath=self.paths)

    def plugins(self):
        """List of all plugins available."""
        for plugin in self.plugin_source.list_plugins():
            yield plugin

    def load(self):
        """Load the plugin object."""
        return self.plugin_source.load_plugin(self.provider)
