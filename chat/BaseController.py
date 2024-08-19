from abc import ABC, abstractmethod
from typing import Optional


class BaseController(ABC):
    """Abstract base class for controlling conversation models"""

    @abstractmethod
    async def get_output(self, messages):
        """
        Get the output from the model for the given messages.

        Args:
            messages (list): A list of messages to send to the model.

        Returns:
            AIMessage: The response from the model.
        """
        raise NotImplementedError

    @abstractmethod
    def get_summary(self, messages):
        """
        Get a summary of the given messages from the model.

        Args:
            messages (list): A list of messages to summarize.

        Returns:
            AIMessage: The summary response from the model.
        """
        raise NotImplementedError
