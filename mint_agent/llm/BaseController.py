import os
from abc import ABC, abstractmethod

from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from langfuse.callback import CallbackHandler
from loguru import logger

load_dotenv()


class BaseController(ABC):
    """Abstract base class for controlling conversation models"""

    def get_callback_handler(self, chat_id, user_id):
        try:
            return CallbackHandler(
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                host=os.getenv("LANGFUSE_HOST"),
                session_id=chat_id,
                user_id=user_id,
                enabled=os.getenv("LANGFUSE_TRACING", "false").lower() == "true",
            )
        except Exception as e:
            logger.error(f"Failed to get langfuse callback handler: {e}")
            return None

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

    @staticmethod
    @abstractmethod
    def handle_api_error(error):
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
