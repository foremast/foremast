"""Test validity of json in templates"""
import pytest
import json

from jinja2 import Template
from jinja2.exceptions import TemplateNotFound

from foremast.utils import get_template


def test_get_template():
    with pytest.raises(TemplateNotFound):
        template = get_template(template_file='doesnotexist.json.j2')


def valid_json(template, data):
    parsed_template = get_template(
        template_file=template,
        data=data)

    assert type(json.loads(parsed_template)) == dict


def test_valid_json_configs():

    data = {
        'env': 'dev',
        'profile': 'profile',
        'app': 'testapp',
    }

    valid_json(template='configs.json.j2', data=data)


def test_valid_json_pipeline():
    data = {}
    valid_json(template='pipeline.json.j2', data=data)
