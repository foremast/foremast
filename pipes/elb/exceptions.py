"""Spinnaker related custom exceptions."""


class SpinnakerError(Exception):
    """Spinnaker related error."""
    pass


class SpinnakerVPCNotFound(SpinnakerError):
    pass
