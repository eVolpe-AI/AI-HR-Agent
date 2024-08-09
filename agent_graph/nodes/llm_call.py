from langchain_core.messages import SystemMessage

from utils.utils import pretty_print_messages


async def llm_call(state):
    messages = state["messages"]
    conversation_summary = state["conversation_summary"]
    if conversation_summary is not None:
        system_prompt = f"{state["system_prompt"]} Oto podsumowanie naszej dotychczasowej rozmowy: {conversation_summary}"
    else: 
        system_prompt = state["system_prompt"]
        
    messages_for_llm = [SystemMessage(content=system_prompt), *messages]

    print("Messages in llm call:")
    pretty_print_messages(messages_for_llm)

    model = state["model"]
    response = await model.ainvoke(messages_for_llm)

    return {"messages": response}
