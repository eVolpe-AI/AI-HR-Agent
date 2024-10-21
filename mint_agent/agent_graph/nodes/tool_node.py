import json
from typing import Any, Callable, List, Optional, Sequence, Union, cast

from langchain_core.messages import ToolCall, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.prebuilt import ToolNode

INVALID_TOOL_NAME_ERROR_TEMPLATE = (
    "Error: {requested_tool} is not a valid tool, try one of [{available_tools}]."
)
TOOL_CALL_ERROR_TEMPLATE = "Error: {error}\n Please fix your mistakes."


def msg_content_output(output: Any) -> str | List[dict]:
    recognized_content_block_types = ("image", "image_url", "text", "json")
    if isinstance(output, str):
        return output
    elif all(
        [
            isinstance(x, dict) and x.get("type") in recognized_content_block_types
            for x in output
        ]
    ):
        return output
    # Technically a list of strings is also valid message content but it's not currently
    # well tested that all chat models support this. And for backwards compatibility
    # we want to make sure we don't break any existing ToolNode usage.
    else:
        try:
            return json.dumps(output, ensure_ascii=False)
        except Exception:
            return str(output)


class AgentToolNode(ToolNode):
    def __init__(
        self,
        tools: Sequence[Union[BaseTool | Callable]],
        *,
        name: str = "tools",
        tags: Optional[list[str]] = None,
        handle_tool_errors: Optional[bool] = True,
    ) -> None:
        super().__init__(
            tools, name=name, tags=tags, handle_tool_errors=handle_tool_errors
        )

    def _run_one(self, call: ToolCall, config: RunnableConfig) -> ToolMessage:
        print("AgentToolNode._run_one")
        if invalid_tool_message := self._validate_tool_call(call):
            return invalid_tool_message

        try:
            input = {**call, **{"type": "tool_call"}}
            tool_message: ToolMessage = self.tools_by_name[call["name"]].invoke(
                input, config
            )
            tool_message.content = cast(
                Union[str, list], msg_content_output(tool_message.content)
            )
            return tool_message
        except Exception as e:
            if not self.handle_tool_errors:
                raise e
            content = TOOL_CALL_ERROR_TEMPLATE.format(error=repr(e))
            return ToolMessage(content, name=call["name"], tool_call_id=call["id"])

    async def _arun_one(self, call: ToolCall, config: RunnableConfig) -> ToolMessage:
        if invalid_tool_message := self._validate_tool_call(call):
            return invalid_tool_message
        try:
            input = {**call, **{"type": "tool_call"}}
            tool_message: ToolMessage = await self.tools_by_name[call["name"]].ainvoke(
                input, config
            )
            tool_response = json.loads(tool_message.content)
            primary_response = tool_response["primary_response"]
            extra_message = tool_response.get("extra_message", "")
            tool_message.content = cast(
                Union[str, list], msg_content_output(primary_response)
            )
            return tool_message
        except Exception as e:
            if not self.handle_tool_errors:
                raise e
            content = TOOL_CALL_ERROR_TEMPLATE.format(error=repr(e))
            return ToolMessage(content, name=call["name"], tool_call_id=call["id"])
