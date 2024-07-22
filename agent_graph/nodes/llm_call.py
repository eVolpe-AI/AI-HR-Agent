def llm_call(state):
    messages = state["messages"]
    model = state["model"]
    response = model.invoke(messages)
    return {"messages": [response]}
