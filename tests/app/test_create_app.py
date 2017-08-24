"""Verifies that instance_links are being retrieved properly from LINKS. Verifies that app_data.json.j2
contains the instance link information"""
from unittest import mock
import requests_mock
import json
import foremast.app.create_app
from foremast.app import SpinnakerApp


@mock.patch('foremast.app.create_app.LINKS', new={"test1": "https://test1.com", "test2": "https://test2.com"})
def test_instance_links():
    """Checks if instance_links is being populated properly"""
    pipeline_config = {
        "instance_links": {
            "test3": "https://test3.com",
            "test4": "https://test4.com",
            "test5": "https://test2.com"
        }
    }
    spinnaker_app = SpinnakerApp(pipeline_config=pipeline_config)
    instance_links = spinnaker_app.retrieve_instance_links()
    assert instance_links == {"test1": "https://test1.com"}, "Instance Links are not being retrieved properly"

    pipeline_config = { "instance_links": {} }
    spinnaker_app = SpinnakerApp(pipeline_config=pipeline_config)
    instance_links = spinnaker_app.retrieve_instance_links()
    assert instance_links == {"test1": "https://test1.com", "test2": "https://test2.com"},
                             "Instance Links are not being retrieved properly"


@mock.patch('foremast.app.create_app.API_URL', new='https://spinnaker.build.gogoair.com:7777')
@mock.patch.object(SpinnakerApp, 'retrieve_instance_links', return_value={"test1": "https://test1.com",
                   "test2": "https://test2.com"}, "test3")
def test_retrieval_of_templates(mock_instance_links):
    """Checks to see if the instance links are populating app_data.json.j2 properly.
    This also mocks the return_value of the accounts on Spinnaker"""
    pipeline_config = {
        "instance_links": {
            "health": ":8080/health",
            "tail_on": ":8133"
        },
        "chaos_monkey": {
            "mean_time": 5,
            "minimum_time": 3,
            "enabled": False,
            "exceptions": []
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
    mock_api_url = 'https://spinnaker.build.gogoair.com:7777/credentials'
    spinnaker_app = SpinnakerApp(pipeline_config=pipeline_config, app=app, email=email, 
                                 project=project, repo=repo)

    with requests_mock.Mocker() as mock_requests:
        mock_requests.get(mock_api_url, json=accounts)    
        accounts = spinnaker_app.get_accounts()
        spinnaker_app.appinfo['accounts'] = accounts
        app_data = json.loads(spinnaker_app.retrieve_template())
    instance_links = app_data['job'][0]['application']['instanceLinks'][0]['links']
    assert_links = {}
    for instance_link in instance_links:
        assert_links[instance_link['title']] = instance_link['path']
    assert assert_links == {**pipeline_config['instance_links'], **mock_instance_links.return_value},
                            "instance_links in app_data.json.j2 is not being populated properly"
