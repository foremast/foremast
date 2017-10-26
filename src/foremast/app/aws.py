"""AWS Spinnaker Application."""
from foremast.app import base


class SpinnakerApp(base.BaseApp):
    """Create AWS Spinnaker Application."""

    provider = 'aws'

    def create(self):
        """Prepare AWS specific data before creation."""
        result = super().create()
        return result

    def delete(self):
        """Delete AWS Spinnaker Application."""
        return False

    def update(self):
        """Update AWS Spinnaker Application."""
        return False
