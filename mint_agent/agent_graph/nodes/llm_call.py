from langchain_core.callbacks.manager import adispatch_custom_event
from langchain_core.messages import SystemMessage

from mint_agent.llm.ChatFactory import ChatFactory
from mint_agent.tools.ToolController import ToolController
from mint_agent.utils.errors import AgentError


async def llm_call(state):
    messages = state["messages"]
    conversation_summary = state["conversation_summary"]

    model_name = state["model_name"]
    provider = state["provider"]
    tools = ToolController.get_tools()

    if conversation_summary is not None:
        system_prompt = f"{state["system_prompt"]} This is summary of our conversation so far: {conversation_summary}"
    else:
        system_prompt = state["system_prompt"]

    messages_for_llm = [SystemMessage(content=system_prompt), *messages]

    try:
        model = ChatFactory.get_model_controller(provider, model_name, tools)
        response = await model.get_output(messages_for_llm)

        if not state["is_advanced"]:
            await adispatch_custom_event("llm_response", {"response": response})
    except Exception as e:
        raise AgentError("Failed to call LLM model") from e

    return {"messages": response}
