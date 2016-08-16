#   Foremast - Pipeline Tooling
#
#   Copyright 2016 Gogo, LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""Module to create dynamically generated DNS record in route53"""
import logging
from pprint import pformat

from ..consts import DOMAIN
from ..utils import (find_elb, get_details, get_properties, get_dns_zone_ids,
                     update_dns_zone_record)


class SpinnakerDns:
    """Manipulate and create generated DNS record in Route53.

    Args:
        app (str): application name for DNS record
        env (str): Environment/Account for DNS record creation
        region (str): AWS Region for DNS record
        elb_subnet (str): Wether the DNS record is in a public or private zone
        prop_path (str): Path to the generated property files

    Returns:
        str: FQDN of application
    """

    def __init__(self, app=None, env=None, region=None, elb_subnet=None, prop_path=None):
        self.log = logging.getLogger(__name__)

        self.domain = DOMAIN
        self.env = env
        self.region = region
        self.elb_subnet = elb_subnet

        self.generated = get_details(app, env=self.env)
        self.app_name = self.generated.app_name()

        self.properties = get_properties(properties_file=prop_path, env=self.env)
        self.header = {'content-type': 'application/json'}

    def create_elb_dns(self):
        """Create dns entries in route53.

        Returns:
            Auto-generated DNS name for the Elastic Load Balancer.
        """
        dns_elb = self.generated.dns()['elb']
        dns_elb_aws = find_elb(name=self.app_name,
                               env=self.env,
                               region=self.region)
        dns_ttl = self.properties['dns']['ttl']

        zone_ids = get_dns_zone_ids(env=self.env, facing=self.elb_subnet)

        self.log.info('Updating Application URL: %s', dns_elb)

        dns_kwargs = {
            'dns_name': dns_elb,
            'dns_name_aws': dns_elb_aws,
            'dns_ttl': dns_ttl,
        }

        # TODO: Verify zone_id matches the domain we are updating There are
        # cases where more than 2 zones are in the account and we need to
        # account for that.
        for zone_id in zone_ids:
            self.log.debug('zone_id: %s', zone_id)

            response = update_dns_zone_record(self.env, zone_id, **dns_kwargs)
            self.log.debug('Dns upsert response: %s', pformat(response))

        return dns_elb
