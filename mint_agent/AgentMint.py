import os
from datetime import datetime
from decimal import Decimal
from typing import AsyncGenerator

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, ToolMessage
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

from mint_agent.agent_api.messages import (
    AgentMessage,
    AgentMessageType,
    UserMessage,
    UserMessageType,
)
from mint_agent.agent_graph.graph import compile_workflow, create_graph
from mint_agent.agent_state.state import (
    GraphState,
    HistoryManagement,
    HistoryManagementType,
)
from mint_agent.database.db_utils import MongoDBUsageTracker
from mint_agent.llm.ChatFactory import ChatFactory, ProviderConfig
from mint_agent.tools.ToolController import ToolController
from mint_agent.utils.AgentLogger import AgentLogger

load_dotenv()


class AgentMint:
    """
    The main agent class that handles the agent's workflow and interactions with the user.
    """

    def __init__(
        self,
        user_id: str,
        mint_user_id: str,
        chat_id: str,
        ip_addr: str,
        is_advanced: bool,
        usage_limit: dict,
    ) -> None:
        tools = ToolController.get_tools()
        self.state = None
        self.chat_id = chat_id
        self.user_id = user_id
        self.ip_addr = ip_addr
        self.is_advanced = is_advanced
        self.usage_limit = usage_limit
        self.default_llm = ChatFactory.get_default_model(os.getenv("LLM_PROVIDER"))

        self.graph = create_graph(tools)
        self.app = compile_workflow(self.graph, user_id)

        self.usage_tracker = MongoDBUsageTracker(
            AsyncIOMotorClient(os.getenv("MONGO_URI")),
            os.getenv("MONGO_DB_NAME"),
            user_id,
        )

        self.history_config = HistoryManagement(
            management_type=HistoryManagementType.KEEP_N_MESSAGES.value,
            number_of_messages=10,
            number_of_tokens=430,
        )

        self.config = {
            "configurable": {
                "chat_id": chat_id,
                "user_id": user_id,
                "mint_user_id": mint_user_id,
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
                messages=prev_state.values.get("messages", []),
                user=self.user_id,
                provider=os.environ.get("LLM_PROVIDER", "ANTHROPIC"),
                model_name=prev_state.values.get(
                    "model_name", os.environ.get("LLM_MODEL", "claude-3-haiku-20240307")
                ),
                tools=ToolController.get_default_tools(),
                safe_tools=ToolController.get_safe_tools(),
                tool_accept=prev_state.values.get("tool_accept", False),
                tool_declines=prev_state.values.get("tool_declines", 0),
                history_config=self.history_config,
                conversation_summary=prev_state.values.get(
                    "conversation_summary", None
                ),
                usage_limit=self.usage_limit,
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

    async def is_within_usage_limit(self) -> bool:
        """
        Check if the user has reached their usage limit.
        """
        TOKENS_PER_PRICE = 1_000_000
        try:
            usage_limit = self.state["usage_limit"]
            token_usage = await self.usage_tracker.get_token_usage(
                int(usage_limit["hours"])
            )

            if token_usage is None:
                return True

            user_spending = 0

            for (provider, model), tokens in token_usage.items():
                model_pricing = ChatFactory.get_pricing_info(provider, model)

                user_spending += sum(
                    Decimal(
                        tokens[category]
                        / Decimal(TOKENS_PER_PRICE)
                        * Decimal(model_pricing[category])
                    )
                    for category in ("input_tokens", "output_tokens")
                )
            return user_spending < Decimal(usage_limit["cost"])

        except KeyError as e:
            raise ValueError(f"Missing expected key: {e}") from e
        except Exception as e:
            raise RuntimeError("An error occurred while checking usage limits.") from e

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

        if not await self.is_within_usage_limit():
            yield AgentMessage(type=AgentMessageType.AGENT_START).to_json()
            yield AgentMessage(type=AgentMessageType.LLM_START).to_json()
            yield AgentMessage(
                type=AgentMessageType.LLM_TEXT,
                content="You have reached your usage limit. Please try again later.",
            ).to_json()
            yield AgentMessage(type=AgentMessageType.LLM_END).to_json()
            yield AgentMessage(type=AgentMessageType.AGENT_END).to_json()
        else:
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
        decline_threshold = int(os.getenv("TOOL_DECLINE_THRESHOLD", "10"))
        switch_llm_model = (
            os.getenv("SWITCH_LLM_MODEL", "False").strip().lower() == "true"
        )

        def switch_to_smarter_model():
            smarter_model = ChatFactory.get_smarter_model(
                self.state["provider"], self.state["model_name"]
            )
            if smarter_model:
                logger.info(f"Switching to smarter model: {smarter_model}")
                self.state["model_name"] = smarter_model
                self.state["tool_declines"] = 0

        match message.type:
            case UserMessageType.INPUT.value:
                self.state["messages"].append(
                    HumanMessage(content=f"{message.content}")
                )
                self.state["tool_accept"] = False

            case UserMessageType.TOOL_CONFIRM.value:
                self.state["tool_accept"] = True
                if self.state["model_name"] != self.default_llm:
                    logger.info("Switching back to default model.")
                    self.state["model_name"] = ChatFactory.get_default_model(
                        self.state["provider"]
                    )
                self.state["tool_declines"] = 0

            case UserMessageType.TOOL_REJECT.value:
                self.state["tool_declines"] += 1

                if (
                    switch_llm_model
                    and self.state["tool_declines"] >= decline_threshold
                ):
                    switch_to_smarter_model()
                    self.state["tool_declines"] = 0

                tool_call_message = self.state["messages"][-1].tool_calls[0]
                self.state["tool_accept"] = False
                self.state["messages"].append(
                    ToolMessage(
                        tool_call_id=tool_call_message["id"],
                        content="Tool call rejected by the user.",
                    )
                )
                self.state["messages"].append(
                    HumanMessage(
                        content=f"I rejected the use of the tool {tool_call_message["name"]} {f"because: {message.content}." if message.content else "and i don't want to provide a reason."}"
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
                returns_usage_data = ProviderConfig.get_param(
                    self.state["provider"], "returns_usage_data"
                )
                self.state["messages"].append(event["data"]["output"])

                if returns_usage_data:
                    usage_data = {
                        "tokens": event["data"]["output"].usage_metadata,
                        "llm": {
                            "provider": self.state["provider"],
                            "model_name": self.state["model_name"],
                        },
                        "timestamp": datetime.now(),
                    }
                    usage_data["tokens"].pop("input_token_details")
                    await self.usage_tracker.push_token_usage(usage_data)
                    self.state["history_token_count"] = event["data"][
                        "output"
                    ].usage_metadata["input_tokens"]
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
                elif event["name"] == "tool_url":
                    output = AgentMessage(
                        type=AgentMessageType.LINK,
                        content=event["data"],
                    )

        return output
