
#from openai import OpenAI
from chat.BaseController import BaseController
from langchain_openai import ChatOpenAI


class ChatGptController(BaseController):
    """ Class to conroll conversation with OpenAI"""

    default_model = 'gpt-3.5-turbo'

    def getClient(self):
        self.timelogger.start_log()
        if self.client is None:
            self.client = ChatOpenAI(
                api_key = self.api_key,
                model = self.model
            )
        self.timelogger.end_log("ChatGptController getClient")
        return self.client