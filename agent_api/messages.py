from enum import Enum


class UserMessageType(Enum):
    chat_history = "chat_history"
    input = "input"
    tool_confirmation = "tool_confirmation"

    def __str__(self):
        return self.value


class AgentMessageType(Enum):
    agent_start = "agent_start"
    agent_end = "agent_end"
    llm_start = "llm_start"
    llm_end = "llm_end"
    llm_text = "llm_text"
    tool_start = "tool_start"
    tool_end = "tool_end"

    def __str__(self):
        return self.value


class AgentMessage:
    type: AgentMessageType
    text: str | None = None
    tool: str | None = None
    tool_input: str | None = None
    tool_name: str | None = None

    def __init__(
        self,
        type: AgentMessageType,
        text: str | None = None,
        tool: str | None = None,
        tool_input: str | None = None,
        tool_name: str | None = None,
    ):
        self.type = type
        self.text = text
        self.tool = tool
        self.tool_input = tool_input
        self.tool_name = tool_name

    def to_json(self) -> dict[str, str]:
        return {k: str(v) for k, v in self.__dict__.items() if v is not None}


class UserMessage:
    type: UserMessageType
    text: str | None = None
    is_tool_confirmed: bool | None = None
    tool_confirmation_message: str | None = None
    chat_history: dict[str, str] | None = None

    def __init__(self, input_json: dict[str, str]):
        self.type = input_json["type"]
        if "text" in input_json:
            self.text = input_json["text"]
        if "is_tool_confirmed" in input_json:
            self.is_tool_confirmed = input_json["is_tool_confirmed"]
        if "tool_confirmation_message" in input_json:
            self.tool_confirmation_message = input_json["tool_confirmation_message"]
        if "chat_history" in input_json:
            self.chat_history = input_json["tool_confirmation_message"]
