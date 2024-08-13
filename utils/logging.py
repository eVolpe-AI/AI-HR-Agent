import os
import sys
import time
from typing import Optional

from dotenv import load_dotenv
from loguru import logger

from agent_state.state import GraphState

INDENT = "    "

load_dotenv()
log_level = os.getenv("LOG_LEVEL")
log_file = os.getenv("LOG_FILE")
log_to_console = os.getenv("LOG_TO_CONSOLE")
log_coloring = os.getenv("LOG_COLORING")


def configure_logging():
    logger.remove(0)
    logger.add(log_file, level=log_level)
    if log_to_console == "TRUE":
        print("logging to console")
        logger.add(sys.stdout, level=log_level)


class Agent_logger:
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

    def set_error(self, error: str) -> None:
        self.end_time = time.time_ns()
        self.error = error
        self._save_log(error=True)

    def set_usage_data(self, usage_data: dict) -> None:
        self.usage_data = usage_data

    def _save_log(self, error: bool = False) -> None:
        execution_time_ms = (self.end_time - self.start_time) / 1e6
        log_message = (
            f"Mint agent interaction IP: {self.ip_addr}, user_id: {self.user_id}, chat_id: {self.chat_id}\n"
            f"{INDENT}<u>Start state:</u> {self.start_state}\n"
            f"{INDENT}<u>End state:</u> {self.end_state}\n"
            f"{INDENT}<u>Execution time:</u> {execution_time_ms}ms"
        )

        if error:
            log_message += f"\n{INDENT}<red>Error:</red> {self.error}"
            logger.opt(colors=True if log_coloring == "TRUE" else False).error(
                log_message
            )
        else:
            logger.opt(colors=True if log_coloring == "TRUE" else False).debug(
                log_message
            )

    def _format_history_config(self, history_config: dict) -> str:
        return "\n" + "\n".join(
            f"{INDENT * 6}{key}: {value}" for key, value in history_config.items()
        )

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
            messages_string += f"\n{INDENT * 6}-> {message_type}: {message.content}"
        return messages_string

    def _format_usage_data(self) -> str:
        if self.usage_data:
            return (
                "\n"
                f"{INDENT * 6}input tokens: {self.usage_data['tokens']['input_tokens']}\n"
                f"{INDENT * 6}output tokens: {self.usage_data['tokens']['output_tokens']}"
            )
        return ""

    def _format_state(self, state: dict) -> str:

        history_config_string = self._format_history_config(state["history_config"])

        messages_string = self._format_messages(state["messages"])

        usage_data_string = self._format_usage_data()
        log_string = f"""
                    user: {state["user"]}
                    llm model name: {state["model"].bound.model}
                    safe_tools: {state["safe_tools"]}
                    tool_accept: {state["tool_accept"]}
                    history_config: {history_config_string}
                    conversation_summary: {state["conversation_summary"]}
                    system_prompt: {state["system_prompt"]}
                    history_token_count: {state["history_token_count"]}<magenta>
                    messages: {messages_string}</magenta>
                    usage_data: {usage_data_string}"""

        return log_string
