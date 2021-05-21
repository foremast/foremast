#   Foremast - Pipeline Tooling
#
#   Copyright 2018 Gogo, LLC
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
"""Add the appropriate ELB Listeners."""
import json
import logging

from ..exceptions import ForemastTemplateNotFound
from ..utils import get_env_credential, get_template

LOG = logging.getLogger(__name__)


def format_listeners(elb_settings=None, env='dev', region='us-east-1'):
    """Format ELB Listeners into standard list.

    Args:
        elb_settings (dict): ELB settings including ELB Listeners to add,
            e.g.::

                # old
                {
                    "certificate": null,
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

        env (str): Environment to find the Account Number for.

    Returns:
        list: ELB Listeners formatted into dicts for Spinnaker::

            [
                {
                    'externalPort': 80,
                    'externalProtocol': 'HTTP',
                    'internalPort': 8080,
                    'internalProtocol': 'HTTP',
                    'sslCertificateId': None,
                    'listenerPolicies': [],
                    'backendPolicies': []
                },
                ...
            ]
    """
    LOG.debug('ELB settings:\n%s', elb_settings)

    credential = get_env_credential(env=env)
    account = credential['accountId']

    listeners = []

    if 'ports' in elb_settings:
        for listener in elb_settings['ports']:
            cert_name = format_cert_name(
                env=env, region=region, account=account, certificate=listener.get('certificate', None))

            lb_proto, lb_port = listener['loadbalancer'].split(':')
            i_proto, i_port = listener['instance'].split(':')
            listener_policies = listener.get('policies', [])
            listener_policies += listener.get('listener_policies', [])
            backend_policies = listener.get('backend_policies', [])

            elb_data = {
                'externalPort': int(lb_port),
                'externalProtocol': lb_proto.upper(),
                'internalPort': int(i_port),
                'internalProtocol': i_proto.upper(),
                'sslCertificateId': cert_name,
                'listenerPolicies': listener_policies,
                'backendPolicies': backend_policies,
            }

            listeners.append(elb_data)
    else:
        listener_policies = elb_settings.get('policies', [])
        listener_policies += elb_settings.get('listener_policies', [])
        backend_policies = elb_settings.get('backend_policies', [])

        listeners = [{
            'externalPort': int(elb_settings['lb_port']),
            'externalProtocol': elb_settings['lb_proto'],
            'internalPort': int(elb_settings['i_port']),
            'internalProtocol': elb_settings['i_proto'],
            'sslCertificateId': elb_settings['certificate'],
            'listenerPolicies': listener_policies,
            'backendPolicies': backend_policies,
        }]

    for listener in listeners:
        LOG.info('ELB Listener:\n'
                 'loadbalancer %(externalProtocol)s:%(externalPort)d\n'
                 'instance %(internalProtocol)s:%(internalPort)d\n'
                 'certificate: %(sslCertificateId)s\n'
                 'listener_policies: %(listenerPolicies)s\n'
                 'backend_policies: %(backendPolicies)s', listener)
    return listeners


def format_cert_name(env='', account='', region='', certificate=None):
    """Format the SSL certificate name into ARN for ELB.

    Args:
        env (str): Account environment name
        account (str): Account number for ARN
        region (str): AWS Region.
        certificate (str): Name of SSL certificate

    Returns:
        str: Fully qualified ARN for SSL certificate
        None: Certificate is not desired
    """
    cert_name = None

    if certificate:
        if certificate.startswith('arn'):
            LOG.info("Full ARN provided...skipping lookup.")
            cert_name = certificate
        else:
            generated_cert_name = generate_custom_cert_name(env, region, account, certificate)
            if generated_cert_name:
                LOG.info("Found generated certificate %s from template", generated_cert_name)
                cert_name = generated_cert_name
            else:
                LOG.info("Using default certificate name logic")
                cert_name = ('arn:aws:iam::{account}:server-certificate/{name}'.format(
                    account=account, name=certificate))
    LOG.debug('Certificate name: %s', cert_name)

    return cert_name


def generate_custom_cert_name(env='', region='', account='', certificate=None):
    """Generate a custom TLS Cert name based on a template.

    Args:
        env (str): Account environment name
        region (str): AWS Region.
        account (str): Account number for ARN.
        certificate (str): Name of SSL certificate.

    Returns:
        str: Fully qualified ARN for SSL certificate.
        None: Template doesn't exist.
    """
    cert_name = None
    template_kwargs = {'account': account, 'name': certificate}

    # TODO: Investigate moving this to a remote API, then fallback to local file if unable to connect
    try:
        rendered_template = get_template(template_file='infrastructure/iam/tlscert_naming.json.j2', **template_kwargs)
        tlscert_dict = json.loads(rendered_template)
    except ForemastTemplateNotFound:
        LOG.info('Unable to find TLS Cert Template...falling back to default logic...')
        return cert_name

    # TODO: Move to v1 method for check
    try:
        LOG.info("Attempting to find TLS Cert using TLS Cert Template v1 lookup...")
        cert_name = tlscert_dict[env][certificate]
        LOG.info("Found TLS certificate named %s under %s using TLS Cert Template v1", certificate, env)
    except KeyError:
        LOG.error("Unable to find TLS certificate named %s under %s using v1 TLS Cert Template.", certificate, env)

    # TODO: Move variable to consts
    # TODO: move to v2 method for check
    tls_services = ['iam', 'acm']
    if cert_name is None and all(service in tlscert_dict for service in tls_services):
        LOG.info("Attempting to find TLS Cert using TLS Cert Template v2 lookup...")
        if certificate in tlscert_dict['iam'][env]:
            cert_name = tlscert_dict['iam'][env][certificate]
            LOG.info("Found IAM TLS certificate named %s under %s using TLS Cert Template v2", certificate, env)
        elif certificate in tlscert_dict['acm'][region][env]:
            cert_name = tlscert_dict['acm'][region][env][certificate]
            LOG.info("Found ACM TLS certificate named %s under %s in %s using TLS Cert Template v2", certificate, env,
                     region)
        else:
            LOG.error(
                "Unable to find TLS certificate named %s under parent keys [ACM, IAM] %s in v2 TLS Cert Template.",
                certificate, env)

    return cert_name
