
from typing import Text, Dict, List
from langchain_anthropic import ChatAnthropic
from chat.BaseController import BaseController

class AnthropicController(BaseController):
    """ Class to conroll conversation with Anthropic"""

    default_model ='claude-3-haiku-20240307'
    max_tokens = 1000

    def getClient(self):
        self.timelogger.start_log()
        if self.client is None:
            self.client = ChatAnthropic(
                api_key=self.api_key,
                model=self.model,
            )
        self.timelogger.end_log("AnthropicController getClient")
        return self.client