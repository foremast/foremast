"""Add the appropriate ELB Listeners."""
import json
import logging
from pprint import pformat

LOG = logging.getLogger(__name__)


def add_listeners(elb_json='', elb_settings=None):
    """Add ELB Listeners.

    Args:
        template_json (str): JSON object of ELB.
        elb_settings (dict): ELB settings including ELB Listeners to add,
            e.g.

            # old
            {
                "i_port": 8080,
                "lb_port": 80,
                "subnet_purpose": "internal",
                "target": "HTTP:8080/health"
            }

            # new
            {
                "ports": [
                    {
                        "instance": "HTTP:8080",
                        "loadbalancer": "HTTP:80"
                    },
                    {
                        "certificate": "cert_name",
                        "instance": "HTTP:8443",
                        "loadbalancer": "HTTPS:443"
                    }
                ],
                "subnet_purpose": "internal",
                "target": "HTTP:8080/health"
            }

    Returns:
        str: JSON text with Listeners filled in.
    """
    elb_dict = json.loads(elb_json)

    elb_listeners = []

    if 'ports' in elb_settings:
        for listener in elb_settings['ports']:
            lb_proto, lb_port = listener['loadbalancer'].split(':')
            i_proto, i_port = listener['instance'].split(':')

            elb_data = {
                'externalPort': int(lb_port),
                'externalProtocol': lb_proto.upper(),
                'internalPort': int(i_port),
                'internalProtocol': i_proto.upper(),
                'sslCertificateId': listener.get('certificate', None)
            }

            elb_listeners.append(elb_data)
    else:
        elb_listeners = [{
            'externalPort': elb_settings.get('lb_port', 80),
            'externalProtocol': 'HTTP',
            'internalPort': elb_settings.get('i_port', 8080),
            'internalProtocol': 'HTTP',
        }]

    LOG.debug('ELB listeners:\n%s', pformat(elb_listeners))

    for job in elb_dict['job']:
        job['listeners'] = elb_listeners

    elb_json = json.dumps(elb_dict)
    LOG.debug('ELB JSON:\n%s', elb_json)
    return elb_json
