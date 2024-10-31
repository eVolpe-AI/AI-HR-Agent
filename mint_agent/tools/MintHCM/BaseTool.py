import os
from abc import ABC, abstractmethod

from dotenv import load_dotenv

from mint_agent.agent_api.CredentialManager import CredentialManager
from mint_agent.tools.MintHCM.SuiteAPI import SuiteCRM

load_dotenv()


class ToolFieldDescription:
    def __init__(
        self,
        alert_description,
        type="text",
        module=None,
        show=True,
        reference_name=None,
    ):
        self.alert_description = alert_description
        self.type = type
        self.module = module
        self.show = show
        self.reference_name = reference_name

    def get_field_info(self):
        return {
            "description": self.alert_description,
            "type": self.type,
            "module": self.module,
            "show": self.show,
            "reference_name": self.reference_name,
        }


class ToolUtils:
    def get_tool_human_info(self) -> dict:
        if hasattr(self, "request_message"):
            request_message = self.request_message
        else:
            request_message = None
            # TODO ADD WARNING

        return_dict = {}
        schema_fields = self.args_schema.__fields__

        for field in schema_fields:
            if (
                schema_fields[field].json_schema_extra
                and schema_fields[field].json_schema_extra["field_description"]
            ):
                field_description = schema_fields[field].json_schema_extra[
                    "field_description"
                ]
                return_dict[field] = field_description.get_field_info()
            else:
                return_dict[field] = {
                    "description": schema_fields[field].description,
                    "type": "text",
                    "module": None,
                }

        print(f"return_dict: {return_dict} \n request message: {request_message}")

        return return_dict, request_message


class BaseAgentTool(ABC):
    """
    Abstract base class for agent tools. This class defines the interface that all agent
    tools must implement.
    """

    @property
    @abstractmethod
    def system(self):
        """
        Abstract property to get the system name.

        Returns:
            str: The name of the system.
        """

    @property
    @abstractmethod
    def credential_type(self):
        """
        Abstract property to get the credential type.

        Returns:
            str: The type of credentials.
        """

    @abstractmethod
    def get_connection(self, config: dict) -> any:
        """
        Abstract method to get a connection for a given user ID.

        Args:
            config (dict): The configuration of the agent graph.

        Returns:
            any: The connection object.
        """
        raise NotImplementedError


class MintBaseTool(BaseAgentTool):
    """
    Class providing the base implementation for connecting to the MintHCM system.

    Attributes:
        api_url (str): The URL of the MintHCM API.
    """

    api_url = os.getenv("MINT_API_URL")

    @property
    def system(self):
        return "MintHCM"

    @property
    def credential_type(self):
        return "APIv8"

    def get_connection(self, config) -> SuiteCRM:
        try:
            user_id = config.get("configurable", {}).get("user_id")
            credential_manager = CredentialManager()
            client_id, client_secret = credential_manager.get_system_credentials(
                user_id=user_id,
                system=self.system,
                credential_type=self.credential_type,
            )
            if not client_id or not client_secret:
                raise ValueError(
                    f"Client ID or client secret not found for user ID: {user_id}"
                )
            return SuiteCRM(
                client_id=client_id, client_secret=client_secret, url=self.api_url
            )
        except Exception as e:
            raise e


def tool_response(
    response: any,
    extra_data: any = None,
) -> dict:
    response = {
        "response": response,
        "extra_data": extra_data,
    }
    return response
