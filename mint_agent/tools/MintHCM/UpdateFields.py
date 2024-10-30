from typing import Any, Dict, Optional, Type

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field

from mint_agent.tools.MintHCM.BaseTool import MintBaseTool, ToolUtils, tool_response
from mint_agent.tools.MintHCM.SuiteAPI import Module


class MintUpdateDataInput(BaseModel):
    module_name: str = Field(
        ...,
        description="Name of the module in MintHCM system. If you don't know the module, use MintSearchTool to search for module name in MintHCM.",
        # json_schema_extra={
        #     "human_description": "Module",
        #     "type": "text",
        # },
    )
    id: str = Field(
        ...,
        description="ID number of the record to update. If you don't know id, use MintSearchTool to search for record id in MintHCM.",
        json_schema_extra={
            "human_description": "Link to record",
            "type": "link",
            "module": "Candidates",  # TODO PASS MODULE NAME HERE
        },
    )
    attributes: Dict[str, Any] = Field(
        ...,
        description="Attributes to update in key-value format",
        json_schema_extra={
            "human_description": "attributes",
            "type": "text",
        },
    )


class MintUpdateFieldsTool(BaseTool, MintBaseTool, ToolUtils):
    name: str = "MintUpdateFieldsTool"
    description: str = """Use this tool to update fields in the module based on data received from the user. Use this tool to update value of the field in the module,
    for example, duration or start date. Before using MintUpdateFieldsTool, ensure you have the correct module name and record ID. If not, use MintSearchTool to retrieve them.
"""
    args_schema: Type[BaseModel] = MintUpdateDataInput

    def _run(
        self,
        module_name: str,
        id: str,
        attributes: Dict[str, Any],
        config: RunnableConfig,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        try:
            suitecrm = self.get_connection(config)
            url = f"{self.api_url}/module"
            data = {"type": module_name, "id": id, "attributes": attributes}
            response = suitecrm.request(url, "patch", parameters=data)
            record_url = suitecrm.get_record_url(module_name, id)
            return tool_response(
                f"Updated field in module {module_name} with ID {id}",
                {"url": record_url},
            )

        except Exception as e:
            raise ToolException(f"Error: {e}")
