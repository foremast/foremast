"""Entrypoint to Application Configuration preparer."""
import argparse
import logging

from .prepare_configs import process_configs

LOG = logging.getLogger(__name__)


def main():
    """Append Application Configurations to a given file in INI format."""
    logging.basicConfig()

    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('-d',
                        '--debug',
                        action='store_const',
                        const=logging.DEBUG,
                        default=logging.INFO,
                        help='Set DEBUG output')
    parser.add_argument('-r',
                        '--runway-dir',
                        required=True,
                        help='Runway directory containing app.json files')
    parser.add_argument('-o',
                        '--output',
                        required=True,
                        help='Name of environment file to append to')
    args = parser.parse_args()

    LOG.setLevel(args.debug)
    logging.getLogger(__package__).setLevel(args.debug)

    process_configs(runway_dir=args.runway_dir, out_file=args.output)


if __name__ == '__main__':
    main()
