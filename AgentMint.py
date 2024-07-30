import asyncio
import logging
from enum import Enum
from typing import Any, Dict, List, Text

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferMemory
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.messages import (
    HumanMessage,
    RemoveMessage,
    SystemMessage,
    ToolMessage,
)
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
        self.username = "admin"
        self.history = None

        tools = self.get_tools()

        self.safe_tools = ToolController.get_safe_tools()
        self.graph = create_graph(tools)
        self.app = compile_workflow(self.graph)
        self.model = ChatAnthropic(
            model="claude-3-haiku-20240307",
            temperature=0,
            max_tokens=1000,
            streaming=True,
        ).bind_tools(tools)

        self.state = GraphState(
            messages=[],
            user=self.username,
            model=self.model,
            safe_tools=self.safe_tools,
            tool_accept=False,
        )

        self.config = {
            "configurable": {
                "thread_id": "42",
            }
        }

    def update_history(self, new_history):
        self.history = new_history

    def get_tools(self):
        available_tools = ToolController.get_available_tools()
        default_tools = ToolController.get_default_tools()
        return [available_tools[tool] for tool in default_tools]

    def visualize_graph(self):
        self.app.get_graph().draw_mermaid_png(output_file_path="graph_schema.png")

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
        if self.history:
            self.state["messages"] = self.history
        else:
            self.state["messages"] = [
                SystemMessage(content=f"{PromptController.get_simple_prompt()}"),
            ]

        if message.type == "tool_confirmation":
            print("\nTool confirmed\n")
            self.state["tool_accept"] = True
        elif message.type == "tool_rejection":
            tool_call_message = self.state["messages"][-1].tool_calls[0]
            print(f"\nTool rejected: {tool_call_message}\n")
            self.state["tool_accept"] = False
            self.state["messages"].append(
                ToolMessage(
                    tool_call_id=tool_call_message["id"],
                    content=f"Wywołanie narzędzia odrzucone przez użytkownika, powód: {message.text if message.text else 'nieznany'}.",
                )
            )
            # self.state["messages"].append(RemoveMessage(id=tool_call_message.id))
            # self.state["messages"].append(
            #     HumanMessage(
            #         content=f"Próbowałeś skorzystać z narzędzia {tool_call_message.content[-1]["name"]}. Ale nie wyrażam na to zgody, bo {message.text if message.text else ''}."
            #     )
            # )
        else:
            self.state["messages"].append(HumanMessage(content=f"{message.text}"))
            self.state["tool_accept"] = False

        print(f"Agent input: {self.state['messages']}")

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

        self.update_history(self.app.get_state(self.config).values["messages"])
