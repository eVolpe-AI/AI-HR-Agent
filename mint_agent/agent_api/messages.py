from enum import Enum
from typing import Dict, Optional

from loguru import logger


class UserMessageType(Enum):
    """
    Enum representing the types of messages a user can send.

    Attributes:
        INPUT (str): An input message from the user.
        TOOL_CONFIRM (str): A confirmation message for a tool.
        TOOL_REJECT (str): A rejection message for a tool.
    """

    INPUT = "input"
    TOOL_CONFIRM = "tool_confirm"
    TOOL_REJECT = "tool_reject"

    def __str__(self):
        return self.value


class AgentMessageType(Enum):
    """
    Enum representing the types of messages an agent can send.

    Attributes:
        AGENT_START (str): The start of the agent's processing.
        AGENT_END (str): The end of the agent's processing.
        LLM_START (str): The start of the LLM's processing.
        LLM_END (str): The end of the LLM's processing.
        LLM_TEXT (str): The text output from the LLM.
        ACCEPT_REQUEST (str): A request to accept a tool.
        TOOL_START (str): The start of the tool's processing.
        TOOL_END (str): The end of the tool's processing.
        ERROR (str): An error message.
    """

    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    LLM_START = "llm_start"
    LLM_END = "llm_end"
    LLM_TEXT = "llm_text"
    ACCEPT_REQUEST = "accept_request"
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    ERROR = "error"

    def __str__(self):
        return self.value


class AgentMessage:
    """
    Represents a message sent by the agent.

    Attributes:
        type (AgentMessageType): The type of the message.
        content (Optional[str]): The content of the message.
        tool_name (Optional[str]): The name of the tool.
        tool_input (Optional[str]): The input to the tool.
    """

    def __init__(
        self,
        type: AgentMessageType,
        content: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_input: Optional[str] = None,
    ):
        self.type = type
        self.content = content
        self.tool_input = tool_input
        self.tool_name = tool_name

    def to_json(self) -> Dict[str, str]:
        """
        Convert the AgentMessage instance to a JSON-serializable dictionary.

        Returns:
            Dict[str, str]: The JSON-serializable dictionary representing the AgentMessage instance.
        """
        return {k: str(v) for k, v in self.__dict__.items() if v is not None}


class UserMessage:
    """
    Represents a message sent by the user.

    Attributes:
        type (UserMessageType): The type of the user message.
        content (Optional[str]): The content of the message.
    """

    def __init__(self, input_json: Dict[str, str]):
        if "type" not in input_json:
            logger.error(f"Missing 'type' key in input_json: {input_json}")
            raise ValueError("Missing 'type' key in input_json")
        self.type = input_json["type"]
        if "content" in input_json:
            self.content = input_json["content"]

    def to_json(self) -> Dict[str, str]:
        """
        Convert the UserMessage instance to a JSON-serializable dictionary.

        Returns:
            Dict[str, str]: The JSON-serializable dictionary representing the UserMessage instance.
        """
        return {k: str(v) for k, v in self.__dict__.items() if v is not None}
