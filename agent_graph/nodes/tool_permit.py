from langchain_core.callbacks.manager import adispatch_custom_event


async def tool_permit(state):
    tool_to_use = state["messages"][-1].tool_calls[0]
    tool_name = tool_to_use["name"]
    tool_input = tool_to_use["args"]

    await adispatch_custom_event(
        "tool_accept", {"tool": tool_name, "params": tool_input}
    )
    new_state = state.copy()

    if tool_name not in state["safe_tools"]:
        new_state["tool_accept"] = 0
    else:
        new_state["tool_accept"] = 1
        # print(
        #     f"""Narzędzie {tool_name} jest bezpieczne i nie wymaga zgody użytkownika."""
        # )

    return new_state
