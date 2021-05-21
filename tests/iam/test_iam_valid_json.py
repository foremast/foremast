"""Test IAM Policy templates are valid JSON."""
import json

import jinja2
import pytest

from foremast.iam.construct_policy import render_policy_template
from foremast.utils.templates import LOCAL_TEMPLATES


def iam_templates():
    """Generate list of IAM templates."""
    jinjaenv = jinja2.Environment(loader=jinja2.FileSystemLoader([str(LOCAL_TEMPLATES)]))

    iam_template_names = jinjaenv.list_templates(filter_func=lambda x: all([
        x.startswith('infrastructure/iam/'),
        'trust' not in x,
        'wrapper' not in x, ]))

    for iam_template_name in iam_template_names:
        yield iam_template_name


@pytest.mark.parametrize(argnames='template_name', argvalues=iam_templates())
def test_all_iam_templates(template_name):
    """Verify all IAM templates render as proper JSON."""
    *_, service_json = template_name.split('/')
    service, *_ = service_json.split('.')

    items = ['resource1', 'resource2']

    if service == 'rds-db':
        items = {
            'resource1': 'user1',
            'resource2': 'user2',
        }

    try:
        rendered = render_policy_template(
            account_number='',
            app='coreforrest',
            env='dev',
            group='forrest',
            items=items,
            pipeline_settings={
                'lambda': {
                    'vpc_enabled': False,
                },
            },
            region='us-east-1',
            service=service)
    except json.decoder.JSONDecodeError:
        pytest.fail('Bad template: {0}'.format(template_name), pytrace=False)

    assert isinstance(rendered, list)
