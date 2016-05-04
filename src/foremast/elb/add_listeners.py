"""Add the appropriate ELB Listeners."""
import json
import logging

LOG = logging.getLogger(__name__)


def format_listeners(elb_settings=None):
    """Format ELB Listeners into standard list."""
    LOG.debug('ELB settings:\n%s', elb_settings)

    listeners = []

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

            listeners.append(elb_data)
    else:
        listeners = [{
            'externalPort': int(elb_settings['lb_port']),
            'externalProtocol': elb_settings['lb_proto'],
            'internalPort': int(elb_settings['i_port']),
            'internalProtocol': elb_settings['i_proto'],
        }]

    for listener in listeners:
        LOG.info('ELB Listener: '
                 'loadbalancer %(externalProtocol)s:%(externalPort)d\t'
                 'instance %(internalProtocol)s:%(internalPort)d\t'
                 'certificate: %(sslCertificateId)s', listener)
    return listeners


def add_listeners(elb_json='', elb_settings=None):
    """Add ELB Listeners.

    Args:
        elb_json (str): JSON object of ELB.
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
    elb_listeners = format_listeners(elb_settings=elb_settings)

    elb_dict = json.loads(elb_json)
    for job in elb_dict['job']:
        job['listeners'] = elb_listeners
    elb_json = json.dumps(elb_dict)

    LOG.debug('ELB JSON:\n%s', elb_json)
    return elb_json
