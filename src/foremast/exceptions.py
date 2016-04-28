"""Spinnaker related custom exceptions."""


class SpinnakerAppNotFound(Exception):
    """Spinnaker app not found error"""
    pass


class SpinnakerApplicationListError(Exception):
    """Spinnaker application list error"""
    pass


class SpinnakerDnsCreationFailed(Exception):
    """Spinnaker DNS creation error"""
    pass


class SpinnakerElbNotFound(Exception):
    """Spinnaker Elb not found"""
    pass


class SpinnakerTimeout(Exception):
    """Spinnaker Timeout error."""
    pass


class SpinnakerError(Exception):
    """Spinnaker related error."""
    pass


class SpinnakerVPCNotFound(SpinnakerError):
    """Spinnaker did not find a VPC."""
    pass


class SpinnakerVPCIDNotFound(SpinnakerError):
    """Spinnaker did not find the VPC ID."""
    pass


class SpinnakerTaskError(SpinnakerError):
    """Spinnaker Task did not finish properly."""

    def __init__(self, task_state):
        super().__init__(task_state['variables'][-1]['value'][-1]['exception'])


class SpinnakerPipelineCreationFailed(Exception):
    """Could not create Spinnaker Pipeline."""
    pass
