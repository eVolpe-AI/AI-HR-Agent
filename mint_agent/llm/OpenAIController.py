from typing import Optional

from dotenv import load_dotenv
from langchain_community.callbacks import get_openai_callback
from langchain_openai import ChatOpenAI

from mint_agent.llm.BaseController import BaseController

load_dotenv()


class OpenAIController(BaseController):
    """Class to control conversation with OpenAI models"""

    DEFAULT_MODEL = "gpt-4o-mini-2024-07-18"
    DEFAULT_MAX_TOKENS = 1000
    DEFAULT_TEMPERATURE = 0.0
    DEFAULT_MAX_RETIRES = 2

    def __init__(
        self,
        model_name: Optional[str] = DEFAULT_MODEL,
        api_key: Optional[str] = None,
        temperature: Optional[float] = DEFAULT_TEMPERATURE,
        max_tokens: Optional[int] = DEFAULT_MAX_TOKENS,
        tools: Optional[list] = None,
        max_retries: Optional[int] = DEFAULT_MAX_RETIRES,
        streaming: bool = True,
    ):
        """
        Initialize the OpenAI with the specified parameters.

        Args:
            model_name (Optional[str]): The name of the model to use. Defaults to DEFAULT_MODEL.
            api_key (Optional[str]): The API key for authentication.
            temperature (Optional[float]): The temperature setting for the model. Defaults to 0.0.
            max_tokens (Optional[int]): The maximum number of tokens for the model's output. Defaults to DEFAULT_MAX_TOKENS.
            tools (Optional[list]): A list of tools to bind to the model. Defaults to an empty list.
            max_retries (Optional[int]): The maximum number of retries for the model. Defaults to DEFAULT_MAX_RETIRES.
            streaming (bool): Whether to use streaming mode. Defaults to True.
        """

        self.client = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_retries=max_retries,
            api_key=api_key,
            max_tokens=max_tokens,
            streaming=streaming,
            stream_usage=True,
        )

        if tools:
            self.client = self.client.bind_tools(tools)

    async def get_output(self, messages):
        return await self.client.ainvoke(messages)

    def get_summary(self, messages):
        config = {
            "tags": ["silent"],
        }
        return self.client.invoke(messages, config)
