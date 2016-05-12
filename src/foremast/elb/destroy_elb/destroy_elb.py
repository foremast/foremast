"""Destroy any ELB Resources."""
from ...utils import Gate, check_task, get_template, get_vpc_id


def destroy_elb(app='', env='dev', region='us-east-1', **_):
    """Destroy ELB Resources.

    Args:
        app (str): Spinnaker Application name.
        env (str): Deployment environment.
        regions (str): AWS region.

    Returns:
        True upon successful completion.
    """
    task_json = get_template(
        template_file='destroy/destroy_elb.json.j2',
        app=app,
        env=env,
        region=region,
        vpc=get_vpc_id(account=env, region=region))

    response = Gate('applications/{0}/tasks'.format(app)).post(task_json)
    check_task(response, app)

    return True
