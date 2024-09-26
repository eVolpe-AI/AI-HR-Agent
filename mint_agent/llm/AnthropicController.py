from typing import Optional

from langchain_anthropic.chat_models import ChatAnthropic
from langchain_core.messages import AIMessage

from mint_agent.llm.BaseController import BaseController

DEFAULT_MODEL = "claude-3-haiku-20240307"
DEFAULT_MAX_TOKENS = 1000


class AnthropicController(BaseController):
    """Class to control conversation with Anthropic's Claude model"""

    def __init__(
        self,
        model_name: Optional[str] = DEFAULT_MODEL,
        api_key: Optional[str] = None,
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
            anthropic_api_key=api_key,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=streaming,
        ).bind_tools(tools)

    async def get_output(self, messages: list) -> AIMessage:
        return await self.client.ainvoke(messages)

    def get_summary(self, messages: list) -> AIMessage:
        config = {
            "tags": ["silent"],
        }
        return self.client.invoke(messages, config)
