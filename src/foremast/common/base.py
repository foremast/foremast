"""Base Plugin class."""
from abc import ABC, abstractmethod


class BasePlugin(ABC):
    """All Plugins should inherit from this base class."""

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
