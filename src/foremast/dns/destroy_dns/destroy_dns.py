"""Destroy any DNS records."""
import json
import logging

import boto3

from ...utils import get_app_details, get_dns_zone_ids, get_template

LOG = logging.getLogger(__name__)


def destroy_dns(app='', env='dev', **_):
    """Destroy DNS records.

    Args:
        app (str): Spinnaker Application name.
        env (str): Deployment environment.
        regions (str): AWS region.

    Returns:
        bool: True upon successful completion.
    """
    client = boto3.Session(profile_name=env).client('route53')

    generated = get_app_details.get_details(app=app, env=env)
    record = generated.dns_elb()

    zone_ids = get_dns_zone_ids(env=env, facing='external')

    for zone_id in zone_ids:
        record_sets = client.list_resource_record_sets(HostedZoneId=zone_id,
                                                       StartRecordName=record,
                                                       StartRecordType='CNAME',
                                                       MaxItems='1')

        for found_record in record_sets['ResourceRecordSets']:
            assert destroy_record(client=client,
                                  found_record=found_record,
                                  record=record,
                                  zone_id=zone_id)

    return True


def destroy_record(client=None, found_record=None, record='', zone_id=''):
    """Destroy an individual DNS record.

    Args:
        client (botocore.client.Route53): Route 53 boto3 client.
        found_record (dict): Route 53 record set::

            {'Name': 'unicorn.forrest.dev.example.com.',
             'ResourceRecords':
             [{'Value':
               'internal-unicornforrest-1777489395.us-east-1.elb.amazonaws.com'
               }],
             'TTL': 60,
             'Type': 'CNAME'}

        record (str): Application DNS record name. e.g.
        zone_id (str): Route 53 Hosted Zone ID, e.g. /hostedzone/ZSVGJWJ979WQD.

    Returns:
        bool: True upon successful completion.
    """
    LOG.debug('Found DNS record: %s', found_record)

    if found_record['Name'].strip('.') == record:
        dns_json = get_template(template_file='destroy/destroy_dns.json.j2',
                                record=json.dumps(found_record))
        dns_dict = json.loads(dns_json)

        client.change_resource_record_sets(HostedZoneId=zone_id,
                                           ChangeBatch=dns_dict)
        LOG.info('Destroyed "%s" in %s', found_record['Name'], zone_id)
    else:
        LOG.info('DNS record "%s" missing from %s.', record, zone_id)
        LOG.debug('Found someone else\'s record: %s', found_record['Name'])

    return True
