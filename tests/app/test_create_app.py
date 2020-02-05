"""Verifies that instance_links are being retrieved properly from LINKS. Verifies that app_data.json.j2
contains the instance link information"""
from unittest import mock
from foremast.app import SpinnakerApp


@mock.patch('foremast.app.spinnaker_app.LINKS', new={'example1': 'https://example1.com'})
def test_default_instance_links():
    """Validate default instance_links are being populated properly."""
    pipeline_config = {
        "instance_links": {
            "example2": "https://example2.com",
        }
    }

    combined = {'example1': 'https://example1.com'}
    combined.update(pipeline_config['instance_links'])

    spinnaker_app = SpinnakerApp("aws", pipeline_config=pipeline_config)
    instance_links = spinnaker_app.retrieve_instance_links()

    assert instance_links == combined, "Instance Links are not being retrieved properly"


@mock.patch('foremast.app.spinnaker_app.LINKS', new={'example': 'example1', 'example': 'example2'})
def test_duplicate_instance_links():
    """Validate behavior when two keys are identical."""

    pipeline_config = {
        "instance_links": {}
    }

    duplicate = {'example': 'example2'}
    spinnaker_app = SpinnakerApp("aws", pipeline_config=pipeline_config)
    instance_links = spinnaker_app.retrieve_instance_links()

    assert instance_links == duplicate, "Instance links handing duplicates are wrong."
