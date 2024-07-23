async def llm_call(state):
    messages = state["messages"]
    model = state["model"]
    response = await model.ainvoke(messages)
    return {"messages": response}
