"""Get Availability Zones for all Subnets."""
import base64
import json
import logging
import os
from collections import defaultdict
from pprint import pformat

import jinja2
import requests
from tryagain import retries


class SpinnakerTimeout(Exception):
    pass


LOG = logging.getLogger(__name__)


@retries(max_attempts=6, wait=10.0, exceptions=SpinnakerTimeout)
def get_subnets(gate_url='http://gate-api.build.example.com:8084',
                target='ec2',
                sample_file_name=''):
    """Gets all availability zones for a given target

        Params:
            gate_url: The URL to hit for gate API access
            target: the type of subnets to look up (ec2 or elb)
            sample_file_name (str): Sample JSON file contents override.

        Return:
            az_dict: dictionary of  availbility zones, structured like
            { $account: { $region: [ $avaibilityzones ] } }
    """
    account_az_dict = defaultdict(defaultdict)

    if sample_file_name:
        with open(sample_file_name, 'rt') as file_handle:
            try:
                sample = file_handle.read()
            except FileNotFoundError:
                pass

        subnet_list = json.loads(sample)
    else:
        subnet_url = gate_url + "/subnets/aws"
        subnet_response = requests.get(subnet_url)

        if not subnet_response.ok:
            raise SpinnakerTimeout(subnet_response.text)

        subnet_list = subnet_response.json()

    LOG.debug('Subnet list: %s', subnet_list)

    for subnet in subnet_list:
        LOG.debug('Subnet:\n%s', pformat(subnet))

        if subnet['target'] == target:
            az = subnet['availabilityZone']
            account = subnet['account']
            region = subnet['region']

            LOG.debug('%s regions: %s', account,
                      list(account_az_dict[account].keys()))

            try:
                if az not in account_az_dict[account][region]:
                    account_az_dict[account][region].append(az)
            except KeyError:
                account_az_dict[account][region] = [az]

    LOG.debug('AZ dict:\n%s', pformat(dict(account_az_dict)))
    return account_az_dict


def get_template(template_file='', **kwargs):
    """Get the Jinja2 template and renders with dict _kwargs_.

    Args:
        template_file (str): F
        kwargs: Keywords to use for rendering the Jinja2 template.

    Returns:
        String of rendered JSON template.
    """
    templatedir = os.path.sep.join((os.path.dirname(__file__), os.path.pardir,
                                    os.path.pardir, 'templates'))
    jinjaenv = jinja2.Environment(loader=jinja2.FileSystemLoader(templatedir))
    template = jinjaenv.get_template(template_file)
    rendered_json = template.render(**kwargs)

    LOG.debug('Rendered JSON:\n%s', rendered_json)
    return rendered_json


def generate_encoded_user_data(env='dev',
                               region='us-east-1',
                               app_name='',
                               group_name=''):
    r"""Generate base64 encoded User Data.

    Args:
        env (str): Deployment environment, e.g. dev, stage.
        region (str): AWS Region, e.g. us-east-1.
        app_name (str): Application name, e.g. coreforrest.
        group_name (str): Application group nane, e.g. core.

    Returns:
        str: base64 encoded User Data script.

            #!/bin/bash
            export CLOUD_ENVIRONMENT=dev
            export CLOUD_APP=coreforrest
            export CLOUD_APP_GROUP=forrest
            export CLOUD_STACK=forrest
            export EC2_REGION=us-east-1
            export CLOUD_DOMAIN=dev.example.com
            printenv | grep 'CLOUD\|EC2' | awk '$0="export "$0'>> /etc/gogo/cloud_env
    """
    user_data = get_template(template_file='user_data.sh.j2',
                             env=env,
                             region=region,
                             app_name=app_name,
                             group_name=group_name, )
    return base64.b64encode(user_data.encode())


def main():
    """MAIN."""
    logging.basicConfig(level=logging.DEBUG)

    get_subnets()
    # get_subnets(sample_file_name='subnets_sample.json')

    generate_encoded_user_data(env='gryffindor',
                               region='hogwarts',
                               app_name='unicornforrest',
                               group_name='forrest')


if __name__ == "__main__":
    main()
