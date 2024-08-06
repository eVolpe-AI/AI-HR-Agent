from utils.utils import pretty_print_messages


async def llm_call(state):
    messages = state["messages"]
    model = state["model"]
    # pretty_print_messages(messages)
    response = await model.ainvoke(messages)
    return {"messages": response}
