import asyncio
from typing import Any

from langchain_core.messages import HumanMessage, RemoveMessage

from agent_state.state import GraphState, HistoryManagementType
from prompts.PromptController import PromptController
from utils.utils import pretty_print_messages


async def prepare_summary(messages: list[Any], state: dict[str, Any]) -> str:
    llm_model = state["model"]
    prev_summary = state["conversation_summary"]

    summary_prompt = PromptController.get_summary_prompt(prev_summary)
    messages_to_summarize = [
        *messages,
        HumanMessage(content=summary_prompt),
    ]
    summary = await llm_model.ainvoke(messages_to_summarize)

    return summary.content[0]["text"]


def clear_message_history(messages: list[Any]) -> tuple[list[Any], list[Any]]:
    messages = messages[:-1]
    messages_to_delete = []
    messages_to_summarize = []

    for message in messages:
        messages_to_delete.append(RemoveMessage(id=message.id))
        messages_to_summarize.append(message)

    return messages_to_delete, messages_to_summarize


def history_manager(state: GraphState) -> GraphState:
    messages = state["messages"]
    history_config = state["history_config"]

    print(f"History token count: {state['history_token_count']}")
    print("History before processing: ")
    pretty_print_messages(state["messages"])

    new_messages = []
    messages_to_summarize = []

    match history_config["management_type"]:
        case HistoryManagementType.KEEP_N_MESSAGES.value:
            if len(messages) > history_config["number_of_messages"]:
                num_of_messages_to_delete = (
                    len(messages) - history_config["number_of_messages"]
                )
                while (
                    messages[num_of_messages_to_delete].type != "human"
                    and num_of_messages_to_delete > 0
                ):
                    num_of_messages_to_delete -= 1
                for i in range(0, num_of_messages_to_delete):
                    new_messages.append(RemoveMessage(id=messages[i].id))

        case HistoryManagementType.KEEP_N_TOKENS.value:
            if state["history_token_count"] > history_config["number_of_tokens"]:
                new_messages.append(RemoveMessage(id=messages[0].id))
                i = 1
                while messages[i].type != "human" and i < len(messages):
                    new_messages.append(RemoveMessage(id=messages[i].id))
                    i += 1

        case HistoryManagementType.SUMMARIZE_N_MESSAGES.value:
            if len(messages) > history_config["number_of_messages"]:
                new_messages, messages_to_summarize = clear_message_history(messages)

        case HistoryManagementType.SUMMARIZE_N_TOKENS.value:
            if state["history_token_count"] > history_config["number_of_tokens"]:
                new_messages, messages_to_summarize = clear_message_history(messages)

        case HistoryManagementType.NONE.value:
            new_messages = messages

        case _:
            raise ValueError(f"Invalid history type {history_config['type']}")

    if messages_to_summarize:
        summary = asyncio.run(prepare_summary(messages_to_summarize, state))
        return {
            "messages": new_messages,
            "conversation_summary": summary,
        }

    return {"messages": new_messages}
