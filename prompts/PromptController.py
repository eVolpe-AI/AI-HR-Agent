import datetime
from typing import Optional


class PromptController:
    simple: str = (
        "Answer only in polish. Don't inform the user about using any tools. Don't inform the user about steps you are taking or will take."
    )

    default: str = """
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
        """

    @staticmethod
    def get_simple_prompt() -> str:
        today = datetime.datetime.now().strftime("%d-%m-%Y")
        return PromptController.simple.format(today=today)

    @staticmethod
    def get_default_prompt(username: str) -> str:
        today = datetime.datetime.now().strftime("%d-%m-%Y")
        return PromptController.default.format(username=username, today=today)

    @staticmethod
    def get_summary_prompt(prev_summary: Optional[str]) -> str:
        if prev_summary is not None:
            return f"""
                This is the current conversation summary: {prev_summary}.
                Based on this and the messages available in the history, create a new brief summary.
                Write it in the form of continuous text and do not add any introduction.
                Skip describing the request for the summary; it's not important information.
            """
        return """
            Create a brief summary of the above conversation. Skip describing the request for the summary; it's not important information. Write only the summary in the form of continuous text.
            Do not add any introduction like 'This is the current conversation summary:'.
        """
