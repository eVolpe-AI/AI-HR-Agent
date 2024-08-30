import os
from datetime import datetime
from typing import AsyncGenerator

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, ToolMessage
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

from agent_api.messages import (
    AgentMessage,
    AgentMessageType,
    UserMessage,
    UserMessageType,
)
from agent_graph.graph import compile_workflow, create_graph
from agent_state.state import GraphState, HistoryManagement, HistoryManagementType
from chat.ChatFactory import ProviderConfig
from database.db_utils import MongoDBUsageTracker
from tools.ToolController import ToolController
from utils.AgentLogger import AgentLogger

load_dotenv()


class AgentMint:
    """
    The main agent class that handles the agent's workflow and interactions with the user.
    """

    def __init__(self, user_id: str, chat_id: str, ip_addr: str, is_advanced: bool) -> None:
        tools = ToolController.get_tools()
        self.state = None
        self.chat_id = chat_id
        self.user_id = user_id
        self.ip_addr = ip_addr
        self.is_advanced = is_advanced

        self.graph = create_graph(tools)
        self.app = compile_workflow(self.graph, user_id)

        self.usage_tracker = MongoDBUsageTracker(
            AsyncIOMotorClient(os.getenv("MONGO_URI")), os.getenv("DB_NAME"), user_id
        )

        self.history_config = HistoryManagement(
            management_type=HistoryManagementType.KEEP_N_MESSAGES.value,
            number_of_messages=15,
            number_of_tokens=430,
        )

        self.config = {
            "configurable": {
                "chat_id": chat_id,
                "user_id": user_id,
            }
        }

        self.agent_logger = AgentLogger(self.user_id, self.chat_id, self.ip_addr)


    async def set_state(self) -> None:
        """
        Set the agent's state based on the previous state stored in the database.
        """
        try:
            prev_state = await self.app.aget_state(self.config)
            self.state = GraphState(
                messages=prev_state.values["messages"],
                user=self.user_id,
                provider=os.environ.get("LLM_PROVIDER", "ANTHROPIC"),
                model_name=os.environ.get("LLM_MODEL", "claude-3-haiku-20240307"),
                tools=ToolController.get_default_tools(),
                safe_tools=ToolController.get_safe_tools(),
                tool_accept=prev_state.values.get("tool_accept", False),
                history_config=self.history_config,
                conversation_summary= prev_state.values.get(
                    "conversation_summary", None
                ),
                system_prompt=prev_state.values.get("system_prompt", None),
                history_token_count=prev_state.values.get("history_token_count", 0),
                    )
        except Exception as e:
            logger.error(f"Failed to get previous state: {e}")
            raise


    def visualize_graph(self) -> None:
        """
        Visualize the agent's graph schema and save it as a PNG file.
        """
        self.app.get_graph().draw_mermaid_png(output_file_path="utils/graph_schema.png")


    async def invoke(self, message: UserMessage) -> AsyncGenerator[str, None]:
        """
        Invoke the agent with the given user message.

        Args:
            message (UserMessage): The message object containing the type and content of the user's message.

        Yields:
            str: The JSON representation of the agent message to be sent to the user.
        
        Raises:
            Exception: If an error occurs during the agent's execution
        """
        await self.set_state()
        self.agent_logger.start(self.state)

        try:
            self.handle_message(message)
            yield AgentMessage(type=AgentMessageType.AGENT_START).to_json()
            
            async for event in self.app.astream_events(
                input=self.state, version="v2", config=self.config
            ):
                output = await self.handle_graph_event(event)
                if output is not None:
                    yield output.to_json()
            yield AgentMessage(type=AgentMessageType.AGENT_END).to_json()
        except Exception as e:
            await self.set_state()
            self.agent_logger.end_error(self.state, e)
            raise 
        
        await self.set_state()
        self.agent_logger.end(self.state)


    def handle_message(self, message: UserMessage) -> None:
        """
        Handle incoming user messages and update the agent's state accordingly.

        Args:
            message (UserMessage): The message object containing the type and content of the user's message.

        Raises:
            ValueError: If the message type is unknown.
        """
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
                        content="Wywołanie narzędzia odrzucone przez użytkownika.",
                    )
                )
                self.state["messages"].append(
                    HumanMessage(
                        content=f"Odrzuciłem użycie narzędzia {tool_call_message["name"]} z powodu: {message.content if message.content else 'brak powodu'}"
                    )
                )
            case _:
                raise ValueError(f"Unknown message type: {message.type}")


    async def handle_graph_event(self, event: dict) -> AgentMessage | None:
        """
        Handle various graph events and update the agent's state accordingly.

        Args:
            event (dict): The event data containing information about the event.
            agent_logger: The logger instance to log usage data.

        Returns:
            AgentMessage | None: The message to be sent based on the event type, or None if no message is to be sent.
        """
        event_kind = event["event"]
        output = None
        match event_kind:
            case "on_chat_model_stream":
                if "silent" not in event["tags"]:
                    content = event["data"]["chunk"].content
                    if content:
                        if isinstance(content, str):
                            output = AgentMessage(
                                type=AgentMessageType.LLM_TEXT, content=content
                            )
                        elif content[-1]["type"] == "text":
                            output = AgentMessage(
                                type=AgentMessageType.LLM_TEXT,
                                content=content[-1]["text"],
                            )
            case "on_chat_model_start":
                output = AgentMessage(type=AgentMessageType.LLM_START)
            case "on_chat_model_end":
                output = AgentMessage(type=AgentMessageType.LLM_END)
                returns_usage_data = ProviderConfig.get_param(self.state["provider"], "returns_usage_data")
                self.state["messages"].append(event["data"]["output"])
                
                if returns_usage_data:
                    usage_data = {
                        "tokens": event["data"]["output"].usage_metadata,
                        "time": datetime.now(),
                    }
                    await self.usage_tracker.push_token_usage(usage_data)
                    self.state["history_token_count"] = event["data"]["output"].usage_metadata["input_tokens"]
                    self.agent_logger.set_usage_data(usage_data)
            case "on_tool_start":
                if self.is_advanced:
                    output = AgentMessage(
                        type=AgentMessageType.TOOL_START,
                        tool_name=event["name"],
                        tool_input=event["data"]["input"],
                    )
            case "on_tool_end":
                if self.is_advanced:
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

        return output
