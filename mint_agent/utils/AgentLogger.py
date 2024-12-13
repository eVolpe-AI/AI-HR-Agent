import os
import sys
import time
import traceback
from typing import Optional

from dotenv import load_dotenv
from loguru import logger

from mint_agent.agent_state.state import GraphState

INDENT = "   "

load_dotenv()
log_level = os.getenv("LOG_LEVEL")
log_file = os.getenv("LOG_FILE")
log_to_console = os.getenv("LOG_TO_CONSOLE")
log_coloring = os.getenv("LOG_COLORING")


def configure_logging():
    logger.remove(0)
    logger.add(log_file, level=log_level)
    if log_to_console == "TRUE":
        logger.add(sys.stdout, level=log_level)


class AgentLogger:
    user_id: str
    chat_id: str
    ip_addr: str
    start_time: float
    end_time: float
    start_state: str
    end_state: str
    error: str
    usage_data: Optional[dict]

    def __init__(self, user_id: str, chat_id: str, ip_addr: str) -> None:
        self.user_id = user_id
        self.chat_id = chat_id
        self.ip_addr = ip_addr
        self.start_time = 0
        self.end_time = 0
        self.start_state = None
        self.end_state = None
        self.error = None
        self.usage_data = None

    def start(self, state: GraphState) -> None:
        self.start_time = time.time_ns()
        self.start_state = self._format_state(state)

    def end(self, state: GraphState) -> None:
        self.end_state = self._format_state(state)
        self.end_time = time.time_ns()
        self._save_log()
        self.clear()

    def end_error(self, state: GraphState, error: Exception) -> None:
        self.end_state = self._format_state(state)
        self.end_time = time.time_ns()
        self.error = error
        self._save_log(error=True)
        self.clear()

    def clear(self) -> None:
        self.start_time = 0
        self.end_time = 0
        self.start_state = None
        self.end_state = None
        self.error = None
        self.usage_data = None

    def set_usage_data(self, usage_data: dict) -> None:
        self.usage_data = usage_data

    def _save_log(self, error: bool = False) -> None:
        execution_time_ms = (self.end_time - self.start_time) / 1e6
        log_message = (
            f"\nMint agent interaction IP: {self.ip_addr}, user_id: {self.user_id}, chat_id: {self.chat_id}\n"
            f"------------\nStart state: {self.start_state}\n"
            f"------------\nEnd state: {self.end_state}\n"
            f"------------\nExecution time: {execution_time_ms}ms"
        )

        if error:
            log_message += f"\nError:\n{traceback.format_exc()}"

        logger.opt(colors=True if log_coloring == "TRUE" else False).debug(log_message)

    def _format_messages(self, messages: list) -> str:
        message_map = {
            "system": "system",
            "human": "human",
            "ai": "llm",
            "tool": "tool",
        }

        messages_string = ""
        for message in messages:
            message_type = message_map.get(message.type, message.type)
            messages_string += f"\n-> {message_type}: {message.content}"
        return messages_string

    def _format_usage_data(self) -> str:
        if self.usage_data:
            return (
                "\n"
                f"input tokens: {self.usage_data['tokens']['input_tokens']}\n"
                f"output tokens: {self.usage_data['tokens']['output_tokens']}"
            )
        return ""

    def _format_state(self, state: dict) -> str:
        no_log_keys = ["messages", "usage_data", "system_prompt", "tools", "safe_tools"]
        messages_string = self._format_messages(state["messages"])

        usage_data_string = self._format_usage_data()

        log_state = {k: v for k, v in state.items() if k not in no_log_keys}

        log_string = f"""
        {log_state}
        __messages__: {messages_string}
        __usage_data__: {usage_data_string}"""
        return log_string
