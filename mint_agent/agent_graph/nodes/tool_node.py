import json
from typing import Any, Callable, List, Optional, Sequence, Union, cast

from langchain_core.callbacks.manager import adispatch_custom_event
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

    async def _arun_one(self, call: ToolCall, config: RunnableConfig) -> ToolMessage:
        if invalid_tool_message := self._validate_tool_call(call):
            return invalid_tool_message
        try:
            inp = {**call, **{"type": "tool_call"}}
            tool_message: ToolMessage = await self.tools_by_name[call["name"]].ainvoke(
                inp, config
            )
            tool_response = json.loads(tool_message.content)
            response = tool_response["response"]
            extra_data = tool_response.get("extra_data") or {}
            if extra_data.get("url"):
                await adispatch_custom_event("tool_url", extra_data["url"])

            tool_message.content = cast(Union[str, list], msg_content_output(response))
            return tool_message
        except Exception as e:
            if not self.handle_tool_errors:
                raise e
            content = TOOL_CALL_ERROR_TEMPLATE.format(error=repr(e))
            return ToolMessage(content, name=call["name"], tool_call_id=call["id"])
