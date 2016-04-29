"""Search for ELB DNS name."""
import logging

import requests
from tryagain import retries

from ..consts import API_URL
from ..exceptions import SpinnakerElbNotFound

LOG = logging.getLogger(__name__)


@retries(max_attempts=5,
         wait=2,
         exceptions=(AssertionError, SpinnakerElbNotFound))
def find_elb(name='', env='', region=''):
    """Get an application's AWS elb dns name."""
    LOG.info('Find %s ELB in %s [%s].', name, env, region)

    url = '{0}/applications/{1}/loadBalancers'.format(API_URL, name)
    response = requests.get(url)

    assert response.ok

    elb_dns = None
    accounts = response.json()
    for account in accounts:
        if account['account'] == env and account['region'] == region:
            elb_dns = account['dnsname']
            break
    else:
        raise SpinnakerElbNotFound(
            'Elb for "{0}" in region {1} not found'.format(name, region))

    LOG.info('Found: %s', elb_dns)
    return elb_dns
