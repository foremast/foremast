"""Test IAM Policy templates are valid JSON."""
import jinja2

from foremast.iam.construct_policy import render_policy_template
from foremast.utils.templates import LOCAL_TEMPLATES


def iam_templates():
    """Generate list of IAM templates."""
    jinjaenv = jinja2.Environment(loader=jinja2.FileSystemLoader([LOCAL_TEMPLATES]))

    iam_template_names = jinjaenv.list_templates(filter_func=lambda x: all([
        x.startswith('infrastructure/iam/'),
        'trust' not in x,
        'wrapper' not in x, ]))

    for iam_template_name in iam_template_names:
        yield iam_template_name



        items = ['resource1', 'resource2']

        if service == 'rds-db':
            items = {
                'resource1': 'user1',
                'resource2': 'user2',
            }

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

        assert isinstance(rendered, list)
