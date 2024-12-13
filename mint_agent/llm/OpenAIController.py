from typing import Optional

import openai
from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from mint_agent.llm.BaseController import BaseController
from mint_agent.utils.errors import AgentError, LLMServiceUnavailableError

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
        )

        if tools:
            self.client = self.client.bind_tools(tools)

    @staticmethod
    def handle_api_error(e: openai.APIStatusError):
        match e.status_code:
            case 400:
                raise AgentError("OpenAI API bad request")
            case 401:
                raise AgentError("OpenAI API authentication error")
            case 429:
                raise AgentError("OpenAI API rate limit exceeded")
            case 500:
                raise AgentError("OpenAI API internal server error")
            case 503:
                raise LLMServiceUnavailableError(
                    "OpenAI API service is temporarily unavailable"
                )
            case _:
                raise AgentError(f"{e}")

    async def get_output(self, messages: list) -> AIMessage:
        try:
            return await self.client.ainvoke(messages)
        except openai.APIStatusError as e:
            self.handle_api_error(e)
        except Exception as e:
            raise AgentError(f"Failed to call OpenAI LLM model: {e}")

    def get_summary(self, messages):
        config = {
            "tags": ["silent"],
        }
        try:
            return self.client.invoke(messages, config)
        except openai.APIStatusError as e:
            self.handle_api_error(e)
        except Exception as e:
            raise AgentError(f"Failed to call OpenAI LLM model: {e}")
