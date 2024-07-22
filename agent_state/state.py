from typing import Annotated, Any, TypedDict

from langgraph.graph import add_messages


class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
    tool_accept: bool
    user: str
    model: Any
    continue_conversation: bool

    def __init__(
        self,
        messages,
        user: str,
        model: Any,
        tool_accept: bool = 0,
        continue_conversation: bool = 1,
    ):
        self.messages = messages
        self.tool_accept = tool_accept
        self.user = user
        self.model = model
        self.continue_conversation = continue_conversation
