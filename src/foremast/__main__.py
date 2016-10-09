"""Foremast CLI commands."""
import argparse
import logging

from . import runner
from .args import add_debug, add_env
from .consts import LOGGING_FORMAT

LOG = logging.getLogger(__name__)


def add_infra(subparsers):
    """Infrastructure subcommands."""
    infra_parser = subparsers.add_parser('infra', help=runner.prepare_infrastructure.__doc__)
    infra_parser.set_defaults(func=runner.prepare_infrastructure)


def add_pipeline(subparsers):
    """Pipeline subcommands."""
    pipeline_parser = subparsers.add_parser(
        'pipeline', help=add_pipeline.__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    pipeline_parser.set_defaults(func=pipeline_parser.print_help)

    pipeline_subparsers = pipeline_parser.add_subparsers(title='Pipelines')

    pipeline_full_parser = pipeline_subparsers.add_parser(
        'app', help=runner.prepare_app_pipeline.__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    pipeline_full_parser.set_defaults(func=runner.prepare_app_pipeline)

    pipeline_onetime_parser = pipeline_subparsers.add_parser(
        'onetime', help='Create onetime Pipeline', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    pipeline_onetime_parser.set_defaults(func=pipeline_onetime_parser.print_help)
    add_env(pipeline_onetime_parser)


def add_rebuild(subparsers):
    """Rebuild Pipeline subcommands."""
    rebuild_parser = subparsers.add_parser(
        'rebuild', help=add_rebuild.__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    rebuild_parser.set_defaults(func=rebuild_parser.print_help)
    rebuild_parser.add_argument('-a', '--all', help='Rebuild all Pipelines')


def add_autoscaling(subparsers):
    """Auto Scaling Group Policy subcommands."""
    autoscaling_parser = subparsers.add_parser(
        'autoscaling', help=add_autoscaling.__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    autoscaling_parser.set_defaults(func=autoscaling_parser.print_help)


def main(manual_args=None):
    """Foremast, your ship's support."""
    logging.basicConfig(format=LOGGING_FORMAT)

    parser = argparse.ArgumentParser(description=main.__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.set_defaults(func=parser.print_help)
    add_debug(parser)

    subparsers = parser.add_subparsers(title='Commands', description='Available activies')

    add_infra(subparsers)
    add_pipeline(subparsers)
    add_rebuild(subparsers)
    add_autoscaling(subparsers)

    args, args_list = parser.parse_known_args(args=manual_args)

    package, *_ = __package__.split('.')
    logging.getLogger(package).setLevel(args.debug)

    LOG.debug('Arguments: %s', args)
    LOG.debug('Leftover arguments: %s', args_list)

    try:
        args.func(args)
    except (AttributeError, TypeError):
        args.func()


if __name__ == '__main__':
    main()
