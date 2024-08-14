from langchain_core.messages import SystemMessage

from utils.errors import AgentError


async def llm_call(state):
    messages = state["messages"]
    conversation_summary = state["conversation_summary"]
    model = state["model"]

    if conversation_summary is not None:
        system_prompt = f"{state["system_prompt"]} Oto podsumowanie naszej dotychczasowej rozmowy: {conversation_summary}"
    else:
        system_prompt = state["system_prompt"]

    messages_for_llm = [SystemMessage(content=system_prompt), *messages]

    try:
        response = await model.ainvoke(messages_for_llm)
    except Exception as e:
        raise AgentError("Failed to call LLM model") from e

    return {"messages": response}
