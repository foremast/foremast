"""Create IAM Instance Profiles, Roles, Users, and Groups."""
import argparse
import logging

from ..args import add_app, add_debug, add_env
from ..consts import LOGGING_FORMAT
from .create_iam import create_iam_resources

LOG = logging.getLogger(__name__)


def main():
    """Command to create IAM Instance Profiles, Roles, Users, and Groups.

    IAM Roles will retain any attached Managed Policies. Inline Policies that do
    not match the name *iam-project_repo_policy* will also be left untouched.

    **WARNING**: Inline Policies named *iam-project_repo_policy* will be
    rewritten.
    """
    logging.basicConfig(format=LOGGING_FORMAT)

    parser = argparse.ArgumentParser(description=main.__doc__)
    add_debug(parser)
    add_app(parser)
    add_env(parser)
    args = parser.parse_args()

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    assert create_iam_resources(**args.__dict__)


if __name__ == '__main__':
    main()
