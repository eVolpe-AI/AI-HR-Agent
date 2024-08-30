from typing import Dict, List, Text

import boto3
from botocore.config import Config
from langchain_aws import ChatBedrock

from llm.BaseController import BaseController


class AnthropicBedrockController(BaseController):
    """Class to conroll conversation with Anthropic on AWS Bedrock"""

    default_model = "anthropic.claude-3-haiku-20240307-v1:0"  #'anthropic.claude-3-sonnet-20240229-v1:0'
    max_tokens = 1000

    def getClient(self):
        raise NotImplementedError("AnthropicBedrockController does not work with tools")
        self.timelogger.start_log()
        my_config = Config(region_name="us-east-1")

        boto3_bedrock = boto3.client("bedrock", config=my_config)
        if self.client is None:
            # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html
            self.client = ChatBedrock(model_id=self.model)
        self.timelogger.end_log("AnthropicController getClient")
        return self.client
