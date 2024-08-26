from abc import ABC, abstractmethod
from typing import Optional

from langchain_core.messages import AIMessage


class BaseController(ABC):
    """Abstract base class for controlling conversation models"""

    @abstractmethod
    async def get_output(self, messages) -> AIMessage:
        """
        Get the output from the model for the given messages.

        Args:
            messages (list): A list of messages to send to the model.

        Returns:
            AIMessage: The response from the model.
        """
        raise NotImplementedError

    # TODO async version causes asyncio error
    @abstractmethod
    def get_summary(self, messages) -> AIMessage:
        """
        Get a summary of the given messages from the model.

        Args:
            messages (list): A list of messages to summarize.

        Returns:
            AIMessage: The summary response from the model.
        """
        raise NotImplementedError
