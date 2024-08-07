import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from motor.motor_asyncio import AsyncIOMotorClient

from agent_api.messages import (
    AgentMessage,
    AgentMessageType,
    UserMessage,
    UserMessageType,
)
from agent_graph.graph import compile_workflow, create_graph
from agent_state.state import GraphState, HistoryManagement, HistoryManagementType
from chat.ChatFactory import ChatFactory
from database.db_utils import MongoDBUsageTracker
from prompts.PromptController import PromptController
from tools.ToolController import ToolController
from utils.mock_streaming import stream_lorem_ipsum

load_dotenv()


class AgentMint:
    def __init__(self, user_id: str, chat_id: str):
        tools = self.get_tools()
        self.user_id = user_id
        self.safe_tools = ToolController.get_safe_tools()
        self.graph = create_graph(tools)
        self.app = compile_workflow(self.graph, user_id)

        self.usage_tracker = MongoDBUsageTracker(
            AsyncIOMotorClient(os.getenv("MONGO_URI")), os.getenv("DB_NAME"), user_id
        )

        self.model = ChatAnthropic(
            model="claude-3-haiku-20240307",
            temperature=0,
            max_tokens=1000,
            streaming=True,
        ).bind_tools(tools)

        history_config = HistoryManagement(
            management_type=HistoryManagementType.N_MESSAGES.value,
            number_of_messages=4,
            create_summary=True,
        )

        self.state = GraphState(
            messages=[],
            user=user_id,
            model=self.model,
            safe_tools=self.safe_tools,
            tool_accept=False,
            history_config=history_config,
            conversation_summary=None,
            system_prompt=None,
        )

        self.config = {
            "configurable": {
                "thread_id": chat_id,
                "user_id": user_id,
            }
        }

    def get_tools(self) -> List[Dict[str, Any]]:
        available_tools = ToolController.get_available_tools()
        default_tools = ToolController.get_default_tools()
        return [available_tools[tool] for tool in default_tools]

    def visualize_graph(self):
        self.app.get_graph().draw_mermaid_png(output_file_path="graph_schema.png")

    async def mock_invoke(self, message: UserMessage):
        yield AgentMessage(type=AgentMessageType.agent_start).to_json()
        yield AgentMessage(type=AgentMessageType.llm_start).to_json()
        await asyncio.sleep(1)

        for chunk in stream_lorem_ipsum():
            yield AgentMessage(type=AgentMessageType.llm_text, text=chunk).to_json()

        yield AgentMessage(type=AgentMessageType.llm_end).to_json()

        yield AgentMessage(
            type=AgentMessageType.tool_start, tool_name="tool1", tool_input="test input"
        ).to_json()
        await asyncio.sleep(4)
        yield AgentMessage(type=AgentMessageType.tool_end, tool_name="tool1").to_json()

        yield AgentMessage(type=AgentMessageType.agent_end).to_json()

    async def invoke(self, message: UserMessage):
        prev_state = await self.app.aget_state(self.config)

        self.state["messages"] = prev_state.values["messages"]
        self.state["conversation_summary"] = prev_state.values.get(
            "conversation_summary", None
        )
        self.state["system_prompt"] = prev_state.values.get("system_prompt", None)

        match message.type:
            case UserMessageType.tool_confirmation.value:
                self.state["tool_accept"] = True
            case UserMessageType.tool_decline.value:
                tool_call_message = self.state["messages"][-1].tool_calls[0]
                self.state["tool_accept"] = False
                self.state["messages"].append(
                    ToolMessage(
                        tool_call_id=tool_call_message["id"],
                        content=f"Wywołanie narzędzia odrzucone przez użytkownika, powód: {message.text if message.text else 'nieznany'}.",
                    )
                )
            case UserMessageType.input.value:
                self.state["messages"].append(HumanMessage(content=f"{message.text}"))
                self.state["tool_accept"] = False
            case _:
                raise ValueError(f"Unknown message type: {message.type}")

        yield AgentMessage(type=AgentMessageType.agent_start).to_json()
        async for event in self.app.astream_events(
            input=self.state, version="v2", config=self.config
        ):
            event_kind = event["event"]
            output = None

            if event_kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    if content[-1]["type"] == "text":
                        output = AgentMessage(
                            type=AgentMessageType.llm_text, text=content[-1]["text"]
                        )
            elif event_kind == "on_chat_model_start":
                output = AgentMessage(type=AgentMessageType.llm_start)
            elif event_kind == "on_chat_model_end":
                usage_data = {
                    "tokens": event["data"]["output"].usage_metadata,
                    "time": datetime.now(),
                }
                await self.usage_tracker.push_token_usage(usage_data)
                output = AgentMessage(type=AgentMessageType.llm_end)
            elif event_kind == "on_tool_start":
                output = AgentMessage(
                    type=AgentMessageType.tool_start,
                    tool_name=event["name"],
                    tool_input=event["data"]["input"],
                )
            elif event_kind == "on_tool_end":
                output = AgentMessage(
                    type=AgentMessageType.tool_end,
                    tool_name=event["name"],
                )
            elif event_kind == "on_custom_event":
                event_name = event["name"]
                event_data = event["data"]
                if event_name == "tool_accept":
                    yield AgentMessage(
                        type=AgentMessageType.tool_accept,
                        tool_input=event_data["params"],
                        tool_name=event_data["tool"],
                    ).to_json()
            if output:
                yield output.to_json()

        yield AgentMessage(type=AgentMessageType.agent_end).to_json()
