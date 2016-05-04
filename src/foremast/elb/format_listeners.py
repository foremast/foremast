"""Add the appropriate ELB Listeners."""
import logging

LOG = logging.getLogger(__name__)


def format_listeners(elb_settings=None):
    """Format ELB Listeners into standard list.

    Args:
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
        list: ELB Listeners formatted into dicts for Spinnaker.

            [
                {
                    'externalPort': 80,
                    'externalProtocol': 'HTTP',
                    'internalPort': 8080,
                    'internalProtocol': 'HTTP',
                    'sslCertificateId': None
                },
                ...
            ]
    """
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
                'sslCertificateId': listener.get('certificate', None),
            }

            listeners.append(elb_data)
    else:
        listeners = [{
            'externalPort': int(elb_settings['lb_port']),
            'externalProtocol': elb_settings['lb_proto'],
            'internalPort': int(elb_settings['i_port']),
            'internalProtocol': elb_settings['i_proto'],
            'sslCertificateId': elb_settings['certificate'],
        }]

    for listener in listeners:
        LOG.info('ELB Listener: '
                 'loadbalancer %(externalProtocol)s:%(externalPort)d\t'
                 'instance %(internalProtocol)s:%(internalPort)d\t'
                 'certificate: %(sslCertificateId)s', listener)
    return listeners
