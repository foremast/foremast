"""Verifies that instance_links are being retrieved properly from LINKS. Verifies that app_data.json.j2
contains the instance link information"""
from unittest import mock

from foremast.plugin_manager import PluginManager

MANAGER = PluginManager('app', 'aws')
PLUGIN = MANAGER.load()


@mock.patch('foremast.app.aws.base.LINKS', new={'example1': 'https://example1.com'})
def test_default_instance_links():
    """Validate default instance_links are being populated properly."""
    pipeline_config = {
        "instance_links": {
            "example2": "https://example2.com",
        }
    }

    combined = {'example1': 'https://example1.com'}
    combined.update(pipeline_config['instance_links'])

    spinnaker_app = PLUGIN.SpinnakerApp(pipeline_config=pipeline_config)
    instance_links = spinnaker_app.retrieve_instance_links()

    assert instance_links == combined, "Instance Links are not being retrieved properly"
