"""Verifies that instance_links are being retrieved properly from LINKS. Verifies that app_data.json.j2
contains the instance link information"""
from unittest import mock
import requests_mock
import json
import foremast.app.create_app
from foremast.app import SpinnakerApp


@mock.patch('foremast.app.create_app.LINKS', new={"test1": "https://test1.com", "test2": "https://test2.com"})
def test_instance_links():
    """Tests to see if the instance_links are being populated properly. The retrieve_instance_links method
    checks to see if the values in the LINKS dictionary are not in the values of pipeline_config['instance_links']
    and if so appends onto a the instance_links dictionary which is eventually returned.
    """
    pipeline_config = {
        "instance_links": {
            "test3": "https://test2.com",
            "test4": "https://test4.com",
        }
    }
    spinnaker_app = SpinnakerApp(pipeline_config=pipeline_config)
    instance_links = spinnaker_app.retrieve_instance_links()
    assert instance_links == {"test1": "https://test1.com"}, "Instance Links are not being retrieved properly"

    pipeline_config = { "instance_links": {} }
    spinnaker_app = SpinnakerApp(pipeline_config=pipeline_config)
    instance_links = spinnaker_app.retrieve_instance_links()
    assert instance_links == {"test1": "https://test1.com", "test2": "https://test2.com"}


@mock.patch('foremast.app.create_app.API_URL', new='https://test.com')
@mock.patch.object(SpinnakerApp, 'retrieve_instance_links', return_value={"test1": "https://test1.com", "test2": "https://test2.com"})
def test_retrieval_of_templates(mock_instance_links):
    """Checks to see if the instance links are populating app_data.json.j2 properly.
    This also mocks the return_value of the accounts on Spinnaker"""

    pipeline_config = {
        "instance_links": {
            "health": ":8080/health",
            "tail_on": ":8133"
        },
        "permissions": {
            "read_roles": [],
            "write_roles": []
        },
        "chaos_monkey": {
            "mean_time": 5,
            "minimum_time": 3,
            "enabled": False,
            "exceptions": []
        },
        "traffic_guards": {
            "accounts": []
        }
    }

    app = "UnitTestApp"
    email = "UnitTestApp@gogoair.com"
    project = "UnitTest"
    repo = "UnitTest"

    accounts = [{
        "type": "aws",
        "name": "dev",
    }]
    mock_api_url = 'https://test.com/credentials'
    spinnaker_app = SpinnakerApp(pipeline_config=pipeline_config, app=app, email=email, 
                                 project=project, repo=repo)
    accounts = [
        {
            "type": "aws",
            "name": "dev",
        }
    ]
    with requests_mock.Mocker() as mock_requests:
        mock_requests.get(mock_api_url, json=accounts)    
        accounts = spinnaker_app.get_accounts()
        spinnaker_app.appinfo['accounts'] = accounts
        app_data = json.loads(spinnaker_app.retrieve_template())
    instance_links = app_data['job'][0]['application']['instanceLinks'][0]['links']
    actual_links = {}
    for instance_link in instance_links:
        actual_links[instance_link['title']] = instance_link['path']
    expected_links = {}
    for key, value in pipeline_config['instance_links'].items():
        if value not in mock_instance_links.return_value.values():
            expected_links[key] = value
    expected_links.update(pipeline_config['instance_links'])
    assert actual_links == expected_links
