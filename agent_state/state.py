from enum import Enum
from typing import Annotated, Any, Optional, TypedDict

from langgraph.graph import add_messages


class HistoryManagementType(Enum):
    N_MESSAGES = "n_messages"
    N_TOKENS = "n_tokens"


class HistoryManagement:
    def __init__(
        self,
        type: HistoryManagementType,
        number_of_messages: Optional[int] = None,
        number_of_tokens: Optional[int] = None,
        create_summary: bool = False,
    ):
        if type not in HistoryManagementType:
            raise ValueError(
                f"Invalid type {type}, must be one of {list(HistoryManagementType)}"
            )
        self.type = type
        self.number_of_messages = number_of_messages
        self.number_of_tokens = number_of_tokens
        self.create_summary = create_summary

    def toJSON(self):
        return {
            "type": self.type.value,
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
    history: HistoryManagement

    def __init__(
        self,
        messages,
        safe_tools: list,
        user: str,
        model: Any,
        tool_accept: bool,
        history: HistoryManagement,
    ):
        self.messages = messages
        self.safe_tools = safe_tools
        self.tool_accept = tool_accept
        self.user = user
        self.model = model
        self.history = history
