"""Foremast CLI commands."""
import argparse
import collections
import logging
import os

from . import runner, validate
from .args import add_debug, add_env
from .consts import LOGGING_FORMAT, SHORT_LOGGING_FORMAT
from .version import print_version

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
        'onetime', help=runner.prepare_onetime_pipeline.__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    pipeline_onetime_parser.set_defaults(func=runner.prepare_onetime_pipeline)
    add_env(pipeline_onetime_parser)


def add_rebuild(subparsers):
    """Rebuild Pipeline subcommands."""
    rebuild_parser = subparsers.add_parser(
        'rebuild', help=runner.rebuild_pipelines.__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    rebuild_parser.set_defaults(func=runner.rebuild_pipelines)
    rebuild_parser.add_argument('-a', '--all', action='store_true', help='Rebuild all Pipelines')
    rebuild_parser.add_argument(
        'project',
        nargs='?',
        default=os.getenv('REBUILD_PROJECT'),
        help='Project to rebuild, overrides $REBUILD_PROJECT')


def add_autoscaling(subparsers):
    """Auto Scaling Group Policy subcommands."""
    autoscaling_parser = subparsers.add_parser(
        'autoscaling',
        help=runner.create_scaling_policy.__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    autoscaling_parser.set_defaults(func=runner.create_scaling_policy)


def add_scheduled_actions(subparsers):
    """Auto Scaling Group Scheduled Actions subcommands."""
    scheduled_actions_parser = subparsers.add_parser(
        'scheduledactions',
        help=runner.create_scheduled_actions.__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    scheduled_actions_parser.set_defaults(func=runner.create_scheduled_actions)


def add_validate(subparsers):
    """Validate Spinnaker setup."""
    validate_parser = subparsers.add_parser(
        'validate', help=add_validate.__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    validate_parser.set_defaults(func=validate_parser.print_help)

    validate_subparsers = validate_parser.add_subparsers(title='Testers')

    validate_all_parser = validate_subparsers.add_parser(
        'all', help=validate.validate_all.__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    validate_all_parser.set_defaults(func=validate.validate_all)

    validate_gate_parser = validate_subparsers.add_parser(
        'gate', help=validate.validate_gate.__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    validate_gate_parser.set_defaults(func=validate.validate_gate)


def main(manual_args=None):
    """Foremast, your ship's support."""
    parser = argparse.ArgumentParser(description=main.__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.set_defaults(func=parser.print_help)
    add_debug(parser)
    parser.add_argument(
        '-s',
        '--short-log',
        action='store_const',
        const=SHORT_LOGGING_FORMAT,
        default=LOGGING_FORMAT,
        help='Truncated logging format')
    parser.add_argument('-v', '--version', action='store_true', help=print_version.__doc__)

    subparsers = parser.add_subparsers(title='Commands', description='Available activies')

    add_infra(subparsers)
    add_pipeline(subparsers)
    add_rebuild(subparsers)
    add_autoscaling(subparsers)
    add_scheduled_actions(subparsers)
    add_validate(subparsers)

    CliArgs = collections.namedtuple('CliArgs', ['parsed', 'extra'])

    parsed, extra = parser.parse_known_args(args=manual_args)
    args = CliArgs(parsed, extra)

    logging.basicConfig(format=args.parsed.short_log)

    package, *_ = __package__.split('.')
    logging.getLogger(package).setLevel(args.parsed.debug)

    LOG.debug('Arguments: %s', args)

    if args.parsed.version:
        args.parsed.func = print_version

    try:
        args.parsed.func(args)
    except (AttributeError, TypeError):
        args.parsed.func()


if __name__ == '__main__':
    main()
