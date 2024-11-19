from enum import Enum
from typing import Annotated, Any, Optional, TypedDict

from langgraph.graph import add_messages


class HistoryManagementType(Enum):
    """
    Enum representing different types of conversation history management strategies.

    Attributes:
        KEEP_N_MESSAGES: Keep only a fixed number of messages in memory (can vary to remain history integrity e.g. human message must be first message in the history).
        KEEP_N_TOKENS: Keep only messages that do not exceed a fixed number of tokens in memory.
        SUMMARIZE_N_MESSAGES: Create summary after reaching certain number of messages.
        SUMMARIZE_N_TOKENS: Create summary after reaching certain number of tokens.
        NONE: No history management, keep all messages in memory.
    """

    KEEP_N_MESSAGES = "keep_n_messages"
    KEEP_N_TOKENS = "keen_n_tokens"
    SUMMARIZE_N_MESSAGES = "summarize_n_messages"
    SUMMARIZE_N_TOKENS = "summarize_n_tokens"
    NONE = "none"


class HistoryManagement(TypedDict):
    """
    TypedDict representing the configuration for history management.

    Attributes:
        management_type: The type of history management strategy.
        number_of_messages: The number of messages to keep or summarize for KEEP_N_MESSAGES and SUMMARIZE_N_MESSAGES (optional).
        number_of_tokens: The number of tokens to keep or summarize for KEEP_N_TOKENS and SUMMARIZE_N_TOKENS (optional).

    Raises:
        ValueError: If the management_type is invalid or if the number_of_messages
                    or number_of_tokens is not a positive integer when required.
    """

    def __init__(
        self,
        management_type: HistoryManagementType,
        number_of_messages: Optional[int] = None,
        number_of_tokens: Optional[int] = None,
    ):
        if management_type not in HistoryManagementType:
            raise ValueError(
                f"Invalid type {management_type}, must be one of {list(HistoryManagementType)}"
            )
        if (
            management_type
            in (
                HistoryManagementType.KEEP_N_MESSAGES,
                HistoryManagementType.SUMMARIZE_N_MESSAGES,
            )
            and number_of_messages is None
            or number_of_messages < 1
        ):
            raise ValueError("number_of_messages must be a positive integer")
        if (
            management_type
            in (
                HistoryManagementType.KEEP_N_TOKENS,
                HistoryManagementType.SUMMARIZE_N_TOKENS,
            )
            and number_of_tokens is None
            or number_of_tokens < 1
        ):
            raise ValueError("number_of_tokens must be a positive integer")
        self.management_type = management_type
        self.number_of_messages = number_of_messages
        self.number_of_tokens = number_of_tokens

    def toJSON(self):
        return {
            "type": self.management_type.value,
            "number_of_messages": self.number_of_messages,
            "number_of_tokens": self.number_of_tokens,
        }


class GraphState(TypedDict):
    """
    TypedDict representing the state of a graph in the agent.

    Attributes:
        messages: A list of messages exchanged in the conversation with standard langgraph add_messages reducer.
        safe_tools: A list of safe tools available for the agent.
        tool_accept: A boolean indicating whether the tool is accepted - used for tool acceptance flow.
        user: The user associated with the graph state.
        model: The llm model used for the conversation.
        history_config: The configuration for history management.
        conversation_summary: A summary of the conversation.
        system_prompt: The system prompt used in the conversation.
        history_token_count: The count of tokens for messages in the current conversation history.
    """

    messages: Annotated[list, add_messages]
    safe_tools: list[str]
    tool_accept: bool
    user: str
    provider: str
    model_name: str
    history_config: HistoryManagement
    conversation_summary: str
    system_prompt: str
    history_token_count: int
    usage_limit: dict
    tools: list[Any]

    def __init__(
        self,
        messages,
        safe_tools: list,
        user: str,
        provider: str,
        model_name: str,
        tool_accept: bool,
        history_config: HistoryManagement,
        system_prompt: str,
        tools: list[Any],
        usage_limit: dict,
        history_token_count: int,
        conversation_summary: str = None,
    ):
        self.messages = messages
        self.safe_tools = safe_tools
        self.tool_accept = tool_accept
        self.user = user
        self.provider = provider
        self.model_name = model_name
        self.history_config = history_config
        self.conversation_summary = conversation_summary
        self.system_prompt = system_prompt
        self.history_token_count = history_token_count
        self.tools = tools
        self.usage_limit = usage_limit
