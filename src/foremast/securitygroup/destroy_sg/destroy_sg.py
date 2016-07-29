"""Destroy Security Group Resources."""
import logging

from ...consts import API_URL
from ...utils import Gate, check_task, get_template, get_vpc_id

LOG = logging.getLogger(__name__)


def destroy_sg(app='', env='', region='', **_):
    """Destroy Security Group.

    Args:
        account (str): AWS account name.
        region (str): Region name, e.g. us-east-1.

    Returns:
        True upon successful completion.
    """
    vpc = get_vpc_id(account=env, region=region)

    try:
        url = '{api}/securityGroups/{env}/{region}/{app}'.format(
            api=API_URL, env=env, region=region,
            app=app)
        security_group = Gate(url).get(vpcId=vpc)
    except AssertionError:
        raise

    if not security_group:
        LOG.info('Nothing to delete.')
    else:
        LOG.info('Found Security Group in %(region)s: %(name)s',
                 security_group)

        destroy_request = get_template('destroy/destroy_sg.json.j2',
                                       app=app,
                                       env=env,
                                       region=region,
                                       vpc=vpc)

        response = Gate().tasks.post(destroy_request)

        check_task(response)

    return True
