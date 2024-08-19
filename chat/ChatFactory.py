from typing import Optional

# from chat.ChatGptAzureController import ChatGptAzureController
# from llm.Qra13bController import Qra13bController
# from chat.GroqController import GroqController
from chat.AnthropicController import AnthropicController

# from llm.MixtralController import MixtralController
# from llm.MistralController import MistralController
# from chat.ChatGptController import ChatGptController


# from chat.AnthropicBedrockController import AnthropicBedrockController


class ChatFactory:

    model_controllers = {
        #'MIXTRAL': MixtralController,
        #'MISTRAL': MistralController,
        "ANTHROPIC": AnthropicController,
        # "ANTHROPIC_AWS": AnthropicBedrockController,
        # "CHATGPT": ChatGptController,
        #'CHATGPT_AZURE' : ChatGptAzureController,
        #'GROQ': GroqController,
    }

    models = {
        #'MIXTRAL': MixtralController,
        #'MISTRAL': MistralController,
        "ANTHROPIC": [
            "claude-3-haiku-20240307",
            # "claude-3-sonnet-20240229",
            # "claude-3-opus-20240229",
        ],
        # "ANTHROPIC_AWS": [
        #     "claude-3-haiku-20240307-v1:0",
        #     "claude-3-sonnet-20240229-v1:0",
        #     "claude-3-opus-20240229-v1:0",
        # ],
        # "CHATGPT": [
        #     "gpt-3.5-turbo",
        #     "gpt4o",
        # ],
        #'CHATGPT_AZURE' : ChatGptAzureController,
        #'GROQ': GroqController,
    }

    @staticmethod
    def get_model_controller(
        provider: str, model_name: str, tools: Optional[list] = None
    ):
        tools = tools or []

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
