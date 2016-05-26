"""Complete Application destroyer script."""
import argparse
import logging

from boto3.exceptions import botocore

from .args import add_app, add_debug
from .consts import ENVS, LOGGING_FORMAT, REGIONS
from .dns.destroy_dns.destroy_dns import destroy_dns
from .elb.destroy_elb.destroy_elb import destroy_elb
from .exceptions import SpinnakerError
from .iam.destroy_iam.destroy_iam import destroy_iam
from .s3.destroy_s3.destroy_s3 import destroy_s3
from .securitygroup.destroy_sg.destroy_sg import destroy_sg

LOG = logging.getLogger(__name__)


def main():
    """Attempt to fully destroy AWS Resources for a Spinnaker Application."""
    logging.basicConfig(format=LOGGING_FORMAT)

    parser = argparse.ArgumentParser(description=main.__doc__)
    add_debug(parser)
    add_app(parser)
    args = parser.parse_args()

    if args.debug == logging.DEBUG:
        logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)
    else:
        LOG.setLevel(args.debug)

    for env in ENVS:
        for region in REGIONS:
            LOG.info('DESTROY %s:%s', env, region)

            try:
                destroy_dns(app=args.app, env=env)
            except botocore.exceptions.ClientError as error:
                LOG.warning('DNS issue for %s in %s: %s', env, region, error)

            try:
                destroy_elb(app=args.app, env=env, region=region)
            except SpinnakerError:
                pass

            try:
                destroy_iam(app=args.app, env=env)
            except botocore.exceptions.ClientError as error:
                LOG.warning('IAM issue for %s in %s: %s', env, region, error)

            try:
                destroy_s3(app=args.app, env=env)
            except botocore.exceptions.ClientError as error:
                LOG.warning('S3 issue for %s in %s: %s', env, region, error)

            try:
                destroy_sg(app=args.app, env=env, region=region)
            except SpinnakerError:
                pass

            LOG.info('Destroyed %s:%s', env, region)

    LOG.info('Destruction complete.')


if __name__ == '__main__':
    main()
