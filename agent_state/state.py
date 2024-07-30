from typing import Annotated, Any, TypedDict

from langgraph.graph import add_messages


class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
    safe_tools: list[str]
    tool_accept: bool
    user: str
    model: Any

    def __init__(
        self,
        messages,
        safe_tools: list,
        user: str,
        model: Any,
        tool_accept: bool,
    ):
        self.messages = messages
        self.safe_tools = safe_tools
        self.tool_accept = tool_accept
        self.user = user
        self.model = model
