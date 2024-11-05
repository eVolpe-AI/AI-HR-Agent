import os
from abc import ABC, abstractmethod
from typing import Literal, Optional

from dotenv import load_dotenv
from loguru import logger

from mint_agent.agent_api.CredentialManager import CredentialManager
from mint_agent.tools.MintHCM.SuiteAPI import SuiteCRM

load_dotenv()


class ToolFieldDescription:
    """A class representing a input parameter description for a tool."""

    def __init__(
        self,
        description: any,
        field_type: Optional[Literal["text", "dict", "link", "link_array"]] = "text",
        additional_params: str = "Additional parameters",
        module: Optional[str] = None,
        show: bool = True,
        reference_name: Optional[str] = None,
    ) -> None:
        """
        Initializes a ToolFieldDescription instance.

        Parameters:
            description (any): The description of the parameter that will be displayed to user, usually a string, dictionary for dict field_type
            field_type (str): The type of the field. Defaults to 'text'.
            additional_params (str): Label for fields that are not present in the dict description.
            module (Optional[str]): Module reference for the field, used to build a link to record when field_type equals link or link_array.
            show (bool): Whether to display the field. Defaults to True.
            reference_name (Optional[str]): module name reference, used to build a link to record when field_type equals link or link_array.
                Useful when module name is not known at the time of writing the tool, but module name is passed to the tool. e.g.

                class ExampleInput(BaseModel):
                    module_name: str = Field(description="Module name")
                    record_id: str = Field(description="Record ID", show=False)
                    record_link: ToolFieldDescription = ToolFieldDescription(
                        description="Record link",
                        field_type="link",
                        reference_name="module_name",
        """
        self.description = description
        self.field_type = field_type
        self.additional_params = additional_params
        self.module = module
        self.show = show
        self.reference_name = reference_name

        if self.field_type == "link" and not (self.reference_name or self.module):
            raise ValueError(
                "For type 'link', either 'reference_name' or 'module' must be provided."
            )

    def get_field_info(self) -> dict:
        """
        Returns information about the field based on its type and visibility.

        Returns:
            dict: A dictionary containing the field information.
        """
        if not self.show:
            return {
                "field_type": self.field_type,
                "show": False,
            }

        field_info = {
            "description": self.description if self.field_type != "dict" else {},
            "field_type": self.field_type,
            "additional_params": self.additional_params,
            "module": self.module,
            "show": self.show,
            "reference_name": self.reference_name,
        }

        if self.field_type == "dict":
            field_info["description"] = {
                item: value.get_field_info() for item, value in self.description.items()
            }

        return field_info


class ToolUtils:
    def get_tool_fields_info(self) -> dict:
        if hasattr(self, "request_message"):
            request_message = self.request_message
        else:
            request_message = None
            logger.warning(f"No request message found for tool {self.name}.")
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


class MintBaseTool(BaseAgentTool, ToolUtils):
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
