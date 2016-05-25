"""Complete Application destroyer script."""
import argparse
import logging

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
    """MAIN."""
    logging.basicConfig(format=LOGGING_FORMAT)

    parser = argparse.ArgumentParser(description=main.__doc__)
    add_debug(parser)
    add_app(parser)
    args = parser.parse_args()

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    for env in ENVS:
        for region in REGIONS:
            destroy_dns(app=args.app, env=env)
            try:
                destroy_elb(app=args.app, env=env, region=region)
            except SpinnakerError:
                pass
            destroy_iam(app=args.app, env=env)
            destroy_s3(app=args.app, env=env)
            destroy_sg(app=args.app, env=env, region=region)


if __name__ == '__main__':
    main()
