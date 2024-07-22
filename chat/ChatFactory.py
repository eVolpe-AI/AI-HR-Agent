import os

# from chat.ChatGptAzureController import ChatGptAzureController
# from llm.Qra13bController import Qra13bController
# from chat.GroqController import GroqController
from chat.AnthropicController import AnthropicController

# from llm.MixtralController import MixtralController
# from llm.MistralController import MistralController
# from chat.ChatGptController import ChatGptController
from dotenv import load_dotenv

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
    def get_model(provider, model_name):

        # check if model_name is in the list of models for the provider
        if model_name not in ChatFactory.models[provider]:
            raise Exception(f"Model {model_name} not supported for provider {provider}")
        base_url = ChatFactory.get_model_param(provider, "BASE_URL", "")
        api_key = ChatFactory.get_model_param(provider, "API_KEY", "")
        temperature = ChatFactory.get_model_param(provider, "TEMPERATURE", 0.0)

        if provider in ChatFactory.model_controllers:
            controller_class = ChatFactory.model_controllers[provider]
            controller = controller_class(model_name, base_url, api_key, temperature)
            print(f"Provider {provider}")
            print(f"Model {model_name}")
            print(f"Controller {controller.__class__.__name__}")
            return controller.getClient()
        else:
            raise Exception(f"Model provider {provider} not supported")

    @staticmethod
    def get_models(provider):
        return ChatFactory.models[provider]

    @staticmethod
    def get_providers():
        return ChatFactory.models.keys()

    @staticmethod
    def get_model_param(provider, param_name, default=None):
        load_dotenv()
        cstm_param_name = provider + "_" + param_name
        param = os.getenv(cstm_param_name, os.getenv(param_name, default))
        return param
