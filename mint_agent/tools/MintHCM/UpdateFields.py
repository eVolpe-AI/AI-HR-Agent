import traceback
from typing import Any, Dict, List, Optional, Type

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field

from mint_agent.tools.MintHCM.BaseTool import MintBaseTool


class MintUpdateDataInput(BaseModel):
    module_name: str = Field(
        ...,
        description="Name of the module in MintHCM system. If you don't know the module, use MintSearchTool to search for module name in MintHCM.",
    )
    id: str = Field(
        ...,
        description="ID number of the record to update. If you don't know id, use MintSearchTool to search for record id in MintHCM.",
    )
    attributes: Dict[str, Any] = Field(
        ..., description="Attributes to update in key-value format"
    )


class MintUpdateFieldsTool(BaseTool, MintBaseTool):
    name = "MintUpdateFieldsTool"
    description = """Use this tool to update fields in the module based on data received from the user. Use this tool to update value of the field in the module,
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
            return "Zaktualizowano pole w module " + module_name + "o ID " + id

        except Exception as e:
            raise ToolException(f"Error: {e}")
