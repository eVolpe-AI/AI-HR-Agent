from langchain_core.messages import SystemMessage
from loguru import logger

from utils.utils import pretty_print_messages


async def llm_call(state):
    messages = state["messages"]
    conversation_summary = state["conversation_summary"]
    model = state["model"]

    if conversation_summary is not None:
        system_prompt = f"{state["system_prompt"]} Oto podsumowanie naszej dotychczasowej rozmowy: {conversation_summary}"
    else: 
        system_prompt = state["system_prompt"]
        
    messages_for_llm = [SystemMessage(content=system_prompt), *messages]

    # logger.debug(f"Calling LLM model with messages: {messages_for_llm}")
    
    try:
        response = await model.ainvoke(messages_for_llm)
    except Exception as e:
        logger.error(f"Failed to call LLM model: {e}")
        return {"messages": []}

    return {"messages": response}
