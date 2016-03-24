"""Create IAM Profiles, Roles, Users, and Groups."""
import argparse
import logging

from .create_iam import create_iam_resources

LOG = logging.getLogger(__name__)


def main():
    """CLI interface for creating IAM Profiles, Roles, Users, and Groups."""
    logging.basicConfig()

    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('-d',
                        '--debug',
                        action='store_const',
                        const=logging.DEBUG,
                        default=logging.INFO,
                        help='Set DEBUG output')
    parser.add_argument('-e',
                        '--env',
                        choices=('dev', 'stage', 'prod'),
                        default='dev',
                        help='Deploy environment')
    parser.add_argument('-g',
                        '--group',
                        default='extra',
                        help='Application Group name, e.g. forrest')
    parser.add_argument('-a',
                        '--app',
                        default='unnecessary',
                        help='Application name, e.g. forrestcore')
    args = parser.parse_args()

    LOG.setLevel(args.debug)
    logging.getLogger(__package__).setLevel(args.debug)
    vars(args).pop('debug')

    create_iam_resources(env=args.env, group=args.group, app=args.app)


if __name__ == '__main__':
    main()
