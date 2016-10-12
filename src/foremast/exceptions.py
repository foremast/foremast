#   Foremast - Pipeline Tooling
#
#   Copyright 2016 Gogo, LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""Foremast and Spinnaker related custom exceptions."""


class ForemastError(Exception):
    """Foremast related error."""
    pass


class ForemastTemplateNotFound(Exception):
    """Foremast Template was not found."""
    pass


class SpinnakerError(ForemastError):
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


class InvalidEventConfiguration(ForemastError):
    """Invalid AWS Lambda event configuration."""
    pass


class SNSTopicNotFound(ForemastError):
    """SNS Topic was not found."""
    pass


class SNSSubscriptionDoesNotExist(ForemastError):
    """SNS Subscriptions does not exist."""
    pass


class LambdaFunctionDoesNotExist(ForemastError):
    """Lambda function was not found."""


class LambdaAliasDoesNotExist(ForemastError):
    """Lambda function was not found."""


class RequiredKeyNotFound(ForemastError):
    """Required key in json config not found"""
    pass
