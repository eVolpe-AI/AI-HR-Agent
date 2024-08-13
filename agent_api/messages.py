from enum import Enum
from typing import Dict, Optional

from loguru import logger


class UserMessageType(Enum):
    INPUT = "input"
    TOOL_CONFIRM = "tool_confirm"
    TOOL_REJECT = "tool_reject"

    def __str__(self):
        return self.value


class AgentMessageType(Enum):
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
        return {k: str(v) for k, v in self.__dict__.items() if v is not None}


class UserMessage:
    def __init__(self, input_json: Dict[str, str]):
        if "type" not in input_json:
            logger.error(f"Missing 'type' key in input_json: {input_json}")
            raise ValueError("Missing 'type' key in input_json")
        self.type = input_json["type"]
        if "content" in input_json:
            self.content = input_json["content"]

    def to_json(self) -> Dict[str, str]:
        return {k: str(v) for k, v in self.__dict__.items() if v is not None}
