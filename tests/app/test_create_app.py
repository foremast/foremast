"""Verifies that instance_links are being retrieved properly from LINKS. Verifies that app_data.json.j2
contains the instance link information"""
from unittest import mock

from foremast.plugin_manager import PluginManager

MANAGER = PluginManager('app', 'aws')
PLUGIN = MANAGER.load()


@mock.patch('foremast.app.aws.base.LINKS', new={"test1": "https://test1.com", "test2": "https://test2.com"})
def test_default_instance_links():
    """Validate default instance_links are being populated properly."""
    pipeline_config = {
        "instance_links": {
            "test3": "https://test2.com",
            "test4": "https://test4.com",
        }
    }
    spinnaker_app = PLUGIN.SpinnakerApp(pipeline_config=pipeline_config)
    instance_links = spinnaker_app.retrieve_instance_links()
    assert instance_links == {"test1": "https://test1.com"}, "Instance Links are not being retrieved properly"
