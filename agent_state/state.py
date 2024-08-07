from enum import Enum
from typing import Annotated, Any, Optional, TypedDict

from langgraph.graph import add_messages


class HistoryManagementType(Enum):
    N_MESSAGES = "n_messages"
    N_TOKENS = "n_tokens"
    NONE = "none"


class HistoryManagement(TypedDict):
    def __init__(
        self,
        management_type: HistoryManagementType,
        number_of_messages: Optional[int] = None,
        number_of_tokens: Optional[int] = None,
        create_summary: Optional[bool] = False,
    ):
        if management_type not in HistoryManagementType:
            raise ValueError(
                f"Invalid type {management_type}, must be one of {list(HistoryManagementType)}"
            )
        if (
            management_type == HistoryManagementType.N_MESSAGES
            and number_of_messages is None
            or number_of_messages < 1
        ):
            raise ValueError("number_of_messages must be a positive integer")
        if (
            management_type == HistoryManagementType.N_TOKENS
            and number_of_tokens is None
            or number_of_tokens < 1
        ):
            raise ValueError("number_of_tokens must be a positive integer")
        self.management_type = management_type
        self.number_of_messages = number_of_messages
        self.number_of_tokens = number_of_tokens
        self.create_summary = create_summary

    def toJSON(self):
        return {
            "type": self.management_type.value,
            "number_of_messages": self.number_of_messages,
            "number_of_tokens": self.number_of_tokens,
            "create_summary": self.create_summary,
        }


class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
    safe_tools: list[str]
    tool_accept: bool
    user: str
    model: Any
    history_config: HistoryManagement
    conversation_summary: str
    system_prompt: str

    def __init__(
        self,
        messages,
        safe_tools: list,
        user: str,
        model: Any,
        tool_accept: bool,
        history_config: HistoryManagement,
        system_prompt: str,
        conversation_summary: str = None,
    ):
        self.messages = messages
        self.safe_tools = safe_tools
        self.tool_accept = tool_accept
        self.user = user
        self.model = model
        self.history_config = history_config
        self.conversation_summary = conversation_summary
        self.system_prompt = system_prompt
