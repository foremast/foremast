"""Create IAM Instance Profiles, Roles, Users, and Groups."""
import argparse
import logging

from ..args import add_debug
from ..consts import LOGGING_FORMAT
from .create_iam import create_iam_resources

LOG = logging.getLogger(__name__)


def main():
    """Command to create IAM Instance Profiles, Roles, Users, and Groups."""
    logging.basicConfig(format=LOGGING_FORMAT)

    parser = argparse.ArgumentParser(description=main.__doc__)
    add_debug(parser)
    parser.add_argument('-e',
                        '--env',
                        choices=('build', 'dev', 'stage', 'prod', 'prods', 'prodp'),
                        default='dev',
                        help='Deploy environment')
    parser.add_argument('-a',
                        '--app',
                        default='testapp',
                        help='Spinnaker Application name')
    args = parser.parse_args()

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)
    vars(args).pop('debug')

    assert create_iam_resources(env=args.env, app=args.app)


if __name__ == '__main__':
    main()
