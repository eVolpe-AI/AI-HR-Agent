from typing import Any, Text, Dict, List
from chat.ChatFactory import ChatFactory
from langchain.agents import AgentExecutor, create_tool_calling_agent

from tools.MintHCM.CreateMeeting import MintCreateMeetingTool
from tools.MintHCM.Search import MintSearchTool
from tools.MintHCM.GetModuleNames import MintGetModuleNamesTool
from tools.MintHCM.GetModuleFields import MintGetModuleFieldsTool
from tools.MintHCM.CreateRecord import MintCreateRecordTool
from tools.MintHCM.GetUsers import MintGetUsersTool

#from tools.MintHCM import MintCreateMeetingTool, MintSearchTool, MintGetModuleNamesTool, MintGetModuleFieldsTool, MintCreateRecordTool, MintGetUsersTool
from tools.CalenderTool import CalendarTool

from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain.memory import ConversationBufferMemory
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ToolException

import traceback

def _handle_tool_error( error: ToolException) -> str:
        # find if what was returned contains fraze "Module ... does not exist"
        print("FULL TRACEBACK:")
        print(traceback.format_exc())
        if "does not exist" in error.args[0]:
            return f"Module Error: {error} . Try to use MintGetModuleNamesTool to get list of available modules."
        else:
            return (
                "The following errors occurred during tool execution:"
                + error.args[0]
                + "Please try another tool."
            )

class AgentMint:

    system_prompt = '''
        Today is {today}.
        User you are talking to is a user of MintHCM with username {username}.
        Always answer in polish.
        You are a helpful assistant. You have access to several tools. Always check with CalendarTool what day it is today. 
        Your task is to provide accurate and relevant information to the user. 
        Use tools to get additional information and provide the user with the most relevant answer. 
        Make sure to verify the information before providing it to the user. 
        If using MintHCM tools, always make sure to use the correct field names and types by using MintSearchTool.
        Do not make up information! Do not rely on your knwledge, always use the tools to get the most accurate information.
        If asked for holidays and events, make sure you knwo wich country the questions regards and search for them with the search tool.
        Do no assume you know what day is now. If you are asked questions regarding today, yesterday, tommorow etc. then always use the CalendarTool to get the current date.
        Some questions may require you to use multiple tools. Think carefully what information you need to best answer and use tools accordinglu or ask additional questions to the user.
        '''

    available_tools = {
        "MintGetModuleNamesTool": MintGetModuleNamesTool(handle_tool_error=_handle_tool_error),
        "MintGetModuleFieldsTool": MintGetModuleFieldsTool(handle_tool_error=_handle_tool_error),
        "MintSearchTool": MintSearchTool(handle_tool_error=_handle_tool_error),
        "MintCreateRecordTool": MintCreateRecordTool(handle_tool_error=_handle_tool_error),
        "MintCreateMeetingTool": MintCreateMeetingTool(handle_tool_error=_handle_tool_error),
        "MintGetUsersTool": MintGetUsersTool(handle_tool_error=_handle_tool_error),
        "Search" : DuckDuckGoSearchResults(name="Search"),
        "CalendarTool" : CalendarTool(name="CalendarTool")
    }

    default_tools = [
        "MintGetModuleNamesTool" ,
        "MintGetModuleFieldsTool" ,
        "MintCreateRecordTool" ,
        "MintCreateMeetingTool" ,
        "MintSearchTool" ,
        "MintGetUsersTool" ,
        "CalendarTool"
    ]

    def __init__(self):
        self.history = StreamlitChatMessageHistory()
        self.memory = ConversationBufferMemory(
            chat_memory=self.history,
            return_messages=True,
            memory_key="chat_history",
            output_key="output",
            input_key="input"
        )
        self.executor = None

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt ),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

    def get_llm(self,  use_provider , use_model ):
        return ChatFactory.get_model(use_provider, use_model)

    def get_tools(self, tools):
        return [self.available_tools[tool] for tool in tools]

    def get_tool_names(self):
        return list(self.available_tools.keys())

    def set_executor(self, use_provider, use_model, use_tools = []):
        print(self.get_tools(use_tools))
        llm = self.get_llm(use_provider,use_model)
        chat_agent = create_tool_calling_agent(llm=llm, tools=self.get_tools(use_tools), prompt=self.prompt)

        self.executor = AgentExecutor(
            agent=chat_agent,
            tools=self.get_tools(use_tools),
            memory=self.memory,
            return_intermediate_steps=True,
            handle_parsing_errors=True,
            verbose=True,
            max_iterations=12
        )

    def get_executor(self, use_provider, use_model, use_tools = []):
        self.set_executor(use_provider, use_model, use_tools)
        return self.executor

    def invoke(self, user_input, callback_handler, use_tools, use_provider,use_model, username):

        print(f"invoke Provider {use_provider}")
        print(f"invoke Model {use_model}")

        cfg = RunnableConfig()
        cfg["callbacks"] = [callback_handler]

        today = self.available_tools["CalendarTool"]._run("%Y-%m-%d (%A)")
        input = {
            "input": user_input,
            "username": username,
            "today": today,
        }
        return self.get_executor(use_provider, use_model,use_tools).invoke(input, cfg)


