"""Spinnaker related custom exceptions."""


class SpinnakerError(Exception):
    """Spinnaker related error."""
    pass


class SpinnakerAppNotFound(SpinnakerError):
    """Spinnaker app not found error."""
    pass


class SpinnakerApplicationListError(SpinnakerError):
    """Spinnaker application list error."""
    pass


class SpinnakerDnsCreationFailed(SpinnakerError):
    """Spinnaker DNS creation error."""
    pass


class SpinnakerElbNotFound(SpinnakerError):
    """Spinnaker Elb not found."""
    pass


class SpinnakerTimeout(SpinnakerError):
    """Spinnaker Timeout error."""
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
        errors = []
        for stage in task_state['execution']['stages']:
            context = stage['context']

            try:
                errors.extend(context['exception']['details']['errors'])
            except KeyError:
                for task in context['kato.tasks']:
                    errors.append(task['exception']['message'])

        super().__init__(*errors)


class SpinnakerPipelineCreationFailed(SpinnakerError):
    """Could not create Spinnaker Pipeline."""
    pass


class SpinnakerSecurityGroupCreationFailed(SpinnakerError):
    """Could not create Security Group."""
    pass


class SpinnakerSecurityGroupError(SpinnakerError):
    """Could not create Security Group."""
    pass


class SpinnakerSubnetError(SpinnakerError):
    """Unavailable environment or region."""

    def __init__(self, env='', region=''):
        error = '{0} is not available for {1}'.format(region, env)
        super().__init__(error)
