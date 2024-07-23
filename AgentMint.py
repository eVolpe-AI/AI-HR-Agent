import asyncio
from typing import Any, Dict, List, Text

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferMemory
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_message_histories import StreamlitChatMessageHistory

# from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from agent_graph.graph import compile_workflow, create_graph
from agent_state.state import GraphState
from chat.ChatFactory import ChatFactory
from prompts.PromptController import PromptController
from tools.ToolController import ToolController

# from tools.MintHCM import MintCreateMeetingTool, MintSearchTool, MintGetModuleNamesTool, MintGetModuleFieldsTool, MintCreateRecordTool, MintGetUsersTool


class AgentMint:
    def __init__(self):
        # self.history = StreamlitChatMessageHistory()
        # self.memory = ConversationBufferMemory(
        #     chat_memory=self.history,
        #     return_messages=True,
        #     memory_key="chat_history",
        #     output_key="output",
        #     input_key="input"
        # )
        self.tool_executor = None
        # self.prompt = ChatPromptTemplate.from_messages(
        #     [
        #         ("system", self.system_prompt),
        #         ("placeholder", "{chat_history}"),
        #         ("human", "{input}"),
        #         ("placeholder", "{agent_scratchpad}"),
        #     ]
        # )

    def get_llm(self, use_provider, use_model):
        return ChatFactory.get_model(use_provider, use_model)

    def get_tools(self):
        available_tools = ToolController.get_available_tools()
        default_tools = ToolController.get_default_tools()
        return [available_tools[tool] for tool in default_tools]

    # def set_executor(self, use_provider, use_model, use_tools=[]):
    #     print(self.get_tools(use_tools))
    #     llm = self.get_llm(use_provider, use_model)
    #     chat_agent = create_tool_calling_agent(
    #         llm=llm, tools=self.get_tools(use_tools), prompt=self.prompt
    #     )

    #     self.executor = AgentExecutor(
    #         agent=chat_agent,
    #         tools=self.get_tools(use_tools),
    #         memory=self.memory,
    #         return_intermediate_steps=True,
    #         handle_parsing_errors=True,
    #         verbose=True,
    #         max_iterations=12,
    #     )

    # def get_executor(self, use_provider, use_model, use_tools=[]):
    #     self.set_executor(use_provider, use_model, use_tools)
    #     return self.executor

    def invoke(self):
        tools = self.get_tools()
        safe_tools = ToolController.get_safe_tools()
        graph = create_graph(tools)
        app = compile_workflow(graph)

        ## Visualize the graph
        # app.get_graph().draw_mermaid_png(output_file_path="graph_schema.png")

        user_input = input("W czym mogę pomóc?\n> ")

        llm_input = [
            SystemMessage(content=f"{PromptController.get_simple_prompt()}"),
            HumanMessage(content=user_input),
        ]

        thread = {"configurable": {"thread_id": "42"}}

        username = "admin"

        model = ChatAnthropic(
            model="claude-3-haiku-20240307",
            temperature=0,
            max_tokens=1000,
            # streaming=True,
        ).bind_tools(tools)

        state = GraphState(
            messages=llm_input,
            user=username,
            model=model,
            safe_tools=safe_tools,
        )

        for event in app.stream(
            state,
            thread,
            stream_mode="values",
        ):
            # event["messages"][-1].pretty_print()
            print()

        # async def run():
        #     async for event in app.astream(state, thread, stream_mode="values"):
        #         # data = event["data"]
        #         # if data["chunk"].content:
        #         #     print(data["chunk"].content, end="|")

        # asyncio.run(run())
