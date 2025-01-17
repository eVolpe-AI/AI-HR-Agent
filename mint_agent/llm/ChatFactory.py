from typing import Optional, Union

from mint_agent.llm.AnthropicController import AnthropicController
from mint_agent.llm.OpenAIController import OpenAIController


class ChatFactory:
    model_controllers = {
        "ANTHROPIC": AnthropicController,
        "OPENAI": OpenAIController,
    }

    models = {
        "ANTHROPIC": {
            "claude-3-haiku-20240307": {
                "pricing": {
                    "input_tokens": 0.25,
                    "output_tokens": 1.25,
                    "cache_reads": 0,
                },
                "model_rank": 1,
            },
            "claude-3-5-haiku-20241022": {
                "pricing": {"input_tokens": 1, "output_tokens": 5, "cache_reads": 0},
                "model_rank": 2,
            },
            "claude-3-5-sonnet-20241022": {
                "pricing": {"input_tokens": 3, "output_tokens": 15, "cache_reads": 0},
                "model_rank": 3,
            },
        },
        "OPENAI": {
            "gpt-4o-mini-2024-07-18": {
                "pricing": {
                    "input_tokens": 0.15,
                    "output_tokens": 0.6,
                    "cache_reads": 0.075,
                },
                "model_rank": 1,
            }
        },
    }

    @staticmethod
    def get_model_controller(
        provider: str, model_name: str, tools: Optional[list] = None
    ):
        tools = tools or None

        if provider not in ChatFactory.model_controllers:
            raise ValueError(f"Model provider {provider} not supported")

        if provider not in ChatFactory.models:
            raise ValueError(f"No models available for provider {provider}")

        if model_name not in ChatFactory.models[provider]:
            raise ValueError(
                f"Model {model_name} not supported for provider {provider}"
            )

        controller_class = ChatFactory.model_controllers[provider]
        return controller_class(model_name=model_name, tools=tools)

    @staticmethod
    def get_pricing_info(provider: str, model_name: str) -> dict:
        try:
            return ChatFactory.models[provider][model_name]["pricing"]
        except:
            raise ValueError(f"Pricing for model {model_name} not found")

    @staticmethod
    def get_models(provider: str) -> list[str]:
        return ChatFactory.models[provider]

    @staticmethod
    def get_providers() -> list[str]:
        return list(ChatFactory.models.keys())

    @staticmethod
    def get_smarter_model(provider: str, model_name: str) -> Union[str, None]:
        model_rank = ChatFactory.models[provider][model_name]["model_rank"]
        for model in ChatFactory.models[provider]:
            if ChatFactory.models[provider][model]["model_rank"] > model_rank:
                return model
        return None

    @staticmethod
    def get_default_model(provider: str) -> Union[str, None]:
        for model, model_info in ChatFactory.models[provider].items():
            if model_info["model_rank"] == 1:
                return model
        return None
