from pluginbase import PluginBase


class PluginManager:
    def __init__(self, paths, provider):
        self.paths = [paths]
        self.provider = provider

        plugin_base = PluginBase(package='foremast.plugins')
        self.plugin_source = plugin_base.make_plugin_source(searchpath=self.paths)

    def plugins(self):
        for plugin in self.plugin_source.list_plugins():
            yield plugin

    def load(self):
        return self.plugin_source.load_plugin(self.provider)
