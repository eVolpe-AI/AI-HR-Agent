from typing import Any

from langchain_core.callbacks.manager import adispatch_custom_event
from langchain_core.messages import ToolMessage

from mint_agent.tools.ToolController import ToolController


def check_required_fields(tool_name: str, tool_params: dict[str, Any]) -> list[str]:
    tool_info = ToolController.available_tools.get(tool_name)
    if not tool_info:
        raise ValueError(f"Tool '{tool_name}' not found in available tools.")

    tool_fields, _ = tool_info.get_tool_info()
    missing_values = []

    for field, field_info in tool_fields.items():
        if field_info["field_type"] == "dict":
            param_values = tool_params.get(field)
            if not isinstance(param_values, dict):
                raise ValueError(
                    f"Expected a dictionary for field '{field}' but got '{param_values}'"
                )

            for param, param_info in field_info["description"].items():
                if param_info.get("required") and not param_values.get(param):
                    missing_values.append(param)
        else:
            if field_info.get("required") and not tool_params.get(field):
                missing_values.append(field)
    return missing_values


async def tool_controller(state):
    tool_to_use = state["messages"][-1].tool_calls[0]
    tool_name = tool_to_use["name"]
    tool_input = tool_to_use["args"]

    new_state = state.copy()

    missing_values = check_required_fields(tool_name, tool_input)

    if tool_name not in state["safe_tools"]:
        missing_values = check_required_fields(tool_name, tool_input)
        if missing_values:
            tool_call_message = state["messages"][-1].tool_calls[0]
            validation_error = f"Missing value for: {', '.join(missing_values)}. Get the information from the person who sent you the request."
            new_state["messages"] = ToolMessage(
                tool_call_id=tool_call_message["id"],
                content=validation_error,
            )
            new_state["tool_decision"] = "validation_error"
            return new_state
        new_state["tool_decision"] = "unsafe"
        await adispatch_custom_event(
            "tool_accept", {"tool": tool_name, "params": tool_input}
        )
    else:
        new_state["tool_decision"] = "safe"

    return new_state
