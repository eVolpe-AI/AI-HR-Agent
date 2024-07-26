import asyncio
import logging
from enum import Enum
from typing import Any, Dict, List, Text

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferMemory
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from agent_api.messages import (
    AgentMessage,
    AgentMessageType,
    UserMessage,
    UserMessageType,
)
from agent_graph.graph import compile_workflow, create_graph
from agent_state.state import GraphState
from chat.ChatFactory import ChatFactory
from prompts.PromptController import PromptController
from tools.ToolController import ToolController
from utils.test import lorem_stream

# logging.basicConfig(level=logging.DEBUG)


class AgentMint:
    def __init__(self):
        self.history = None

    def get_llm(self, use_provider, use_model):
        return ChatFactory.get_model(use_provider, use_model)

    def get_tools(self):
        available_tools = ToolController.get_available_tools()
        default_tools = ToolController.get_default_tools()
        return [available_tools[tool] for tool in default_tools]

    def visualize_graph(self):
        graph = create_graph(self.get_tools())
        app = compile_workflow(graph)
        app.get_graph().draw_mermaid_png(output_file_path="graph_schema.png")

    async def mock_invoke(self, message: UserMessage):
        yield AgentMessage(type=AgentMessageType.agent_start).to_json()
        yield AgentMessage(type=AgentMessageType.llm_start).to_json()
        await asyncio.sleep(1)

        for chunk in lorem_stream():
            yield AgentMessage(type=AgentMessageType.llm_text, text=chunk).to_json()

        yield AgentMessage(type=AgentMessageType.llm_end).to_json()

        yield AgentMessage(
            type=AgentMessageType.tool_start, tool_name="tool1", tool_input="test input"
        ).to_json()
        await asyncio.sleep(4)
        yield AgentMessage(type=AgentMessageType.tool_end, tool_name="tool1").to_json()

        yield AgentMessage(type=AgentMessageType.agent_end).to_json()

    async def invoke(self, message: UserMessage):
        tools = self.get_tools()
        safe_tools = ToolController.get_safe_tools()
        graph = create_graph(tools)
        app = compile_workflow(graph)

        llm_input = [
            SystemMessage(content=f"{PromptController.get_simple_prompt()}"),
            HumanMessage(content=f"{message.text}"),
        ]

        username = "admin"

        model = ChatAnthropic(
            model="claude-3-haiku-20240307",
            temperature=0,
            max_tokens=1000,
            streaming=True,
        ).bind_tools(tools)

        state = GraphState(
            messages=llm_input,
            user=username,
            model=model,
            safe_tools=safe_tools,
        )

        config = {
            "configurable": {
                "system_prompt": PromptController.get_simple_prompt(),
                "thread_id": "42",
            }
        }

        yield AgentMessage(type=AgentMessageType.agent_start).to_json()

        async for event in app.astream_events(state, version="v2", config=config):
            event_kind = event["event"]
            print(event_kind)
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

            if output:
                yield output.to_json()

        yield AgentMessage(type=AgentMessageType.agent_end).to_json()
