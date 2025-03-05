from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, Field


class UserMessageType(str, Enum):
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


class AgentMessageType(str, Enum):
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
    LINK = "link"
    ACCEPT_REQUEST = "accept_request"
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    ERROR = "error"


class AgentMessage(BaseModel):
    """
    Represents a message sent by the agent.

    Attributes:
        type (AgentMessageType): The type of the message.
        content (Optional[str]): The content of the message.
        tool_name (Optional[str]): The name of the tool.
        tool_input (Optional[str]): The input to the tool.
    """

    type: AgentMessageType
    content: Optional[str] = Field(None, description="The content of the message.")
    tool_name: Optional[str] = Field(None, description="The name of the tool.")
    tool_input: Optional[Union[dict, str]] = Field(
        None, description="Describes input to the tool."
    )
    run_id: Optional[str] = Field(None, description="The langchain run ID")

    class Config:
        use_enum_values = True

    def to_json(self) -> dict:
        return self.model_dump(exclude_none=True)


class UserMessage(BaseModel):
    """
    Represents a message sent by the user.

    Attributes:
        type (UserMessageType): The type of the user message.
        content (Optional[str]): The content of the message.
    """

    type: UserMessageType
    content: Optional[str] = Field(None, description="The content of the message.")

    class Config:
        use_enum_values = True

    def to_json(self) -> dict:
        return self.model_dump(exclude_none=True)
