"""Base Plugin class."""
from abc import ABC, abstractmethod, abstractproperty


class BasePlugin(ABC):
    """All Plugins should inherit from this base class."""

    @abstractproperty
    def resource(self):
        """Implement the resource property."""
        pass

    @abstractproperty
    def provider(self):
        """Implement the provider property."""
        pass

    @abstractmethod
    def create(self):
        """Implement the Resource create operation."""
        pass

    @abstractmethod
    def delete(self):
        """Implement the Resource deletion operation."""
        pass

    @abstractmethod
    def update(self):
        """Implement the Resource update operation."""
        pass
