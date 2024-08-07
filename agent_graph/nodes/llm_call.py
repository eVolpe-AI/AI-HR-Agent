from langchain_core.messages import SystemMessage

from utils.utils import pretty_print_messages


async def llm_call(state):
    messages = state["messages"]
    messages_for_llm = [SystemMessage(content=state["system_prompt"]), *messages]
    print("Messages in llm call:")
    pretty_print_messages(messages_for_llm)

    model = state["model"]
    response = await model.ainvoke(messages_for_llm)

    return {"messages": response}
