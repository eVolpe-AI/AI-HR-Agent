import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class PromptController:
    simple: str = "Answer only in {language}"

    default: str = """
        User you are talking to is a user of MintHCM with username {username}.
        Always answer in {language}.
        You are a helpful assistant. You have access to several tools. Always check with CalendarTool what day it is today. 
        Your task is to provide accurate and relevant information to the user. 
        Use tools to get additional information and provide the user with the most relevant answer. 
        Make sure to verify the information before providing it to the user. 
        If using MintHCM tools, always make sure to use the correct field names and types by using MintSearchTool.
        Do not make up information! Do not rely on your knowledge, always use the tools to get the most accurate information.
        If asked for holidays and events, make sure you know which country the questions regards and search for them with the search tool.
        Do no assume you know what day is now. If you are asked questions regarding today, yesterday, tomorrow etc. then always use the CalendarTool to get the current date.
        Some questions may require you to use multiple tools. Think carefully what information you need to best answer and use tools accordingly or ask additional questions to the user.
        When listing meetings or calls use tabular format.
        """

    @staticmethod
    def get_simple_prompt() -> str:
        language = os.getenv("LLM_LANGUAGE", "english")
        return PromptController.simple.format(language=language)

    @staticmethod
    def get_default_prompt(username: str) -> str:
        language = os.getenv("LLM_LANGUAGE", "english")
        return PromptController.default.format(username=username, language=language)

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
