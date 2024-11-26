from typing import Optional

from mint_agent.llm.AnthropicController import AnthropicController
from mint_agent.llm.OpenAIController import OpenAIController


class ProviderConfig:
    """
    Configuration class for different providers.

    This class holds configuration details for various providers and allows
    retrieval of specific parameters for each provider.
    """

    config = {
        "ANTHROPIC": {"returns_usage_data": True},
        "OPENAI": {"returns_usage_data": False},
    }

    @staticmethod
    def get_param(provider: str, param: str) -> any:
        """
        Retrieve a specific parameter for a given provider.

        Args:
            provider (str): The name of the provider.
            param (str): The parameter to retrieve.

        Returns:
            any: The value of the requested parameter.

        Raises:
            ValueError: If the provider or parameter is not supported.
        """
        if provider not in ProviderConfig.config:
            raise ValueError(f"Provider {provider} not supported")
        if param not in ProviderConfig.config[provider]:
            raise ValueError(f"Param {param} not supported for provider {provider}")
        return ProviderConfig.config[provider][param]


class ChatFactory:
    model_controllers = {
        "ANTHROPIC": AnthropicController,
        "OPENAI": OpenAIController,
    }

    models = {
        "ANTHROPIC": [
            "claude-3-haiku-20240307",
            # "claude-3-sonnet-20240229",
            # "claude-3-opus-20240229",
        ],
        "OPENAI": [
            "gpt-4o-mini-2024-07-18",
            # "gpt-4o",
        ],
    }

    @staticmethod
    def get_model_controller(
        provider: str, model_name: str, tools: Optional[list] = None
    ):
        tools = tools or None

        if provider not in ChatFactory.model_controllers:
            raise ValueError(f"Model provider {provider} not supported")

        if model_name not in ChatFactory.models[provider]:
            raise ValueError(
                f"Model {model_name} not supported for provider {provider}"
            )

        controller_class = ChatFactory.model_controllers[provider]
        return controller_class(model_name=model_name, tools=tools)

    @staticmethod
    def get_models(provider: str) -> list[str]:
        return ChatFactory.models[provider]

    @staticmethod
    def get_providers() -> list[str]:
        return list(ChatFactory.models.keys())
