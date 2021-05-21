"""Package version functions."""
import pkg_resources


def get_version():
    """Retrieve package version."""
    version = 'Not installed.'

    try:
        version = pkg_resources.get_distribution(__package__).version
    except pkg_resources.DistributionNotFound:
        pass

    return version


def print_version():
    """Show package version."""
    print(get_version())
