import asyncio
from typing import Optional

from langchain_core.messages import HumanMessage, RemoveMessage

from agent_state.state import HistoryManagementType
from prompts.PromptController import PromptController
from utils.utils import pretty_print_messages


async def prepare_summary(
    model, messages: list, system_prompt: str, prev_summary: Optional[str] = None
) -> list:
    prompt = PromptController.get_summary_prompt(prev_summary)

    messages = [
        *messages,
        HumanMessage(content=prompt),
    ]

    system_prompt = PromptController.get_simple_prompt()
    summary = await model.ainvoke(messages)
    new_system_prompt = f"{system_prompt} Oto podsumowanie naszej dotychczasowej rozmowy: {summary.content[-1]["text"]}"

    return [new_system_prompt, summary]


def summarize_messages(messages, state):
    llm_model = state["model"]
    prev_summary = state["conversation_summary"]

    if prev_summary is not None:
        system_prompt, summary = asyncio.run(
            prepare_summary(
                llm_model, messages, state["system_prompt"], prev_summary
            )
        )
    else:
        system_prompt, summary = asyncio.run(
            prepare_summary(llm_model, messages, state["system_prompt"])
        )
    return {
        "system_prompt": system_prompt,
        "conversation_summary": summary,
    }

def manage_n_messages(messages, history_config, create_summary):
    new_messages = []
    messages_to_summarize = []

    if create_summary:
        if len(messages) > history_config["number_of_messages"]:
            for message in messages[:-1]:
                new_messages.append(RemoveMessage(id=message.id))
                if create_summary:
                    messages_to_summarize.append(message)
    else:
        num_of_messages_to_delete = len(messages) - history_config["number_of_messages"]
        for i in range(0, num_of_messages_to_delete):
            if i == num_of_messages_to_delete - 1 and messages[i].type == "human":
                break
            new_messages.append(RemoveMessage(id=messages[i].id))
    return new_messages, messages_to_summarize


def history_manager(state):
    messages = state["messages"]
    history_config = state["history_config"]
    create_summary = history_config["create_summary"]

    print("History before processing: ")
    pretty_print_messages(state["messages"])

    new_messages = []
    messages_to_summarize = []

    match history_config["management_type"]:
        case HistoryManagementType.N_MESSAGES.value:
            new_messages, messages_to_summarize = manage_n_messages(
                messages, history_config, create_summary
                )

        case HistoryManagementType.N_TOKENS.value:
            pass

        case HistoryManagementType.NONE.value:
            new_messages = messages

        case _:
            raise ValueError(f"Invalid history type {history_config['type']}")

    if create_summary and messages_to_summarize:
        summary_data = summarize_messages(messages_to_summarize, state)
        
        return {
            "messages": new_messages,
            **summary_data,
        }

    return {"messages": new_messages}
