import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Text

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
from agent_state.state import GraphState
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

        self.state = GraphState(
            messages=[],
            user=user_id,
            model=self.model,
            safe_tools=self.safe_tools,
            tool_accept=False,
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
        yield AgentMessage(type=AgentMessageType.AGENT_START).to_json()
        yield AgentMessage(type=AgentMessageType.LLM_START).to_json()
        await asyncio.sleep(1)

        for chunk in stream_lorem_ipsum():
            yield AgentMessage(type=AgentMessageType.LLM_TEXT, content=chunk).to_json()

        yield AgentMessage(type=AgentMessageType.LLM_END).to_json()

        yield AgentMessage(
            type=AgentMessageType.TOOL_START, tool_name="tool1", tool_input="test input"
        ).to_json()
        await asyncio.sleep(4)
        yield AgentMessage(type=AgentMessageType.TOOL_END).to_json()

        yield AgentMessage(type=AgentMessageType.AGENT_END).to_json()

    async def invoke(self, message: UserMessage):
        prev_state = await self.app.aget_state(self.config)
        if not prev_state.values["messages"]:
            self.state["messages"] = [
                SystemMessage(content=f"{PromptController.get_simple_prompt()}"),
            ]

        match message.type:
            case UserMessageType.INPUT.value:
                self.state["messages"].append(
                    HumanMessage(content=f"{message.content}")
                )
                self.state["tool_accept"] = False
            case UserMessageType.TOOL_CONFIRM.value:
                self.state["tool_accept"] = True
            case UserMessageType.TOOL_REJECT.value:
                tool_call_message = self.state["messages"][-1].tool_calls[0]
                self.state["tool_accept"] = False
                self.state["messages"].append(
                    ToolMessage(
                        tool_call_id=tool_call_message["id"],
                        content=f"Wywołanie narzędzia odrzucone przez użytkownika, powód: {message.content if message.content else 'nieznany'}.",
                    )
                )
            case _:
                raise ValueError(f"Unknown message type: {message.type}")

        yield AgentMessage(type=AgentMessageType.AGENT_START).to_json()

        async for event in self.app.astream_events(
            input=self.state, version="v2", config=self.config
        ):
            event_kind = event["event"]
            output = None

            match event_kind:
                case "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content and content[-1]["type"] == "text":
                        output = AgentMessage(
                            type=AgentMessageType.LLM_TEXT, content=content[-1]["text"]
                        )
                case "on_chat_model_start":
                    output = AgentMessage(type=AgentMessageType.LLM_START)
                case "on_chat_model_end":
                    usage_data = {
                        "tokens": event["data"]["output"].usage_metadata,
                        "time": datetime.now(),
                    }
                    await self.usage_tracker.push_token_usage(usage_data)
                    output = AgentMessage(type=AgentMessageType.LLM_END)
                case "on_tool_start":
                    output = AgentMessage(
                        type=AgentMessageType.TOOL_START,
                        tool_name=event["name"],
                        tool_input=event["data"]["input"],
                    )
                case "on_tool_end":
                    output = AgentMessage(
                        type=AgentMessageType.TOOL_END,
                    )
                case "on_custom_event":
                    if event["name"] == "tool_accept":
                        output = AgentMessage(
                            type=AgentMessageType.ACCEPT_REQUEST,
                            tool_input=event["data"]["params"],
                            tool_name=event["data"]["tool"],
                        )

            if output:
                yield output.to_json()

        yield AgentMessage(type=AgentMessageType.AGENT_END).to_json()

        self.update_history(self.app.get_state(self.config).values["messages"])
