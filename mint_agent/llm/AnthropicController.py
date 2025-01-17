from typing import Optional

import anthropic
from langchain_anthropic.chat_models import ChatAnthropic
from langchain_core.messages import AIMessage

from mint_agent.llm.BaseController import BaseController
from mint_agent.utils.errors import AgentError, LLMServiceUnavailableError

DEFAULT_MODEL = "claude-3-haiku-20240307"
DEFAULT_MAX_TOKENS = 1000


class AnthropicController(BaseController):
    """Class to control conversation with Anthropic's Claude model"""

    def __init__(
        self,
        model_name: Optional[str] = DEFAULT_MODEL,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = DEFAULT_MAX_TOKENS,
        tools: Optional[list] = None,
        streaming: bool = True,
    ):
        """
        Initialize the AnthropicController with the specified parameters.

        Args:
            model_name (Optional[str]): The name of the model to use. Defaults to DEFAULT_MODEL.
            api_key (Optional[str]): The API key for authentication.
            temperature (Optional[float]): The temperature setting for the model. Defaults to 0.0.
            max_tokens (Optional[int]): The maximum number of tokens for the model's output. Defaults to DEFAULT_MAX_TOKENS.
            tools (Optional[list]): A list of tools to bind to the model. Defaults to an empty list.
            streaming (bool): Whether to use streaming mode. Defaults to True.
        """

        tools = tools or []

        self.client = ChatAnthropic(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=streaming,
        ).bind_tools(tools)

    @staticmethod
    def handle_api_error(e: anthropic.APIStatusError):
        match e.status_code:
            case 400:
                raise AgentError("Anthropic API bad request")
            case 401:
                raise AgentError("Anthropic API authentication error")
            case 403:
                raise AgentError("Anthropic API permission denied")
            case 413:
                raise AgentError("Anthropic API request exceeds the maximum size limit")
            case 500:
                raise AgentError("Anthropic API internal server error")
            case 529:
                raise LLMServiceUnavailableError(
                    "Anthropic API is temporarily unavailable."
                )
            case _:
                raise AgentError(f"{e}")

    async def get_output(self, messages: list) -> AIMessage:
        try:
            return await self.client.ainvoke(messages)
        except anthropic.APIStatusError as e:
            self.handle_api_error(e)
        except Exception as e:
            raise AgentError(f"Failed to call Anthropic LLM model: {e}")

    def get_summary(self, messages: list) -> AIMessage:
        config = {
            "tags": ["silent"],
        }
        try:
            return self.client.invoke(messages, config)
        except anthropic.APIStatusError as e:
            self.handle_api_status_error(e)
        except Exception as e:
            raise AgentError(f"Failed to call Anthropic LLM model: {e}")
