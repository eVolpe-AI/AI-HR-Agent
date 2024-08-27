import traceback
from typing import Any, Dict, List, Optional, Type

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field

from tools.MintHCM.BaseTool import MintBaseTool


class MintDeleteDataInput(BaseModel):
    module_name: str = Field(
        ...,
        description="Name of the module in Mint in which the record is to be deleted",
    )
    id: Any = Field(..., description="ID number of the record to be deleted")


class MintDeleteRecordTool(BaseTool, MintBaseTool):
    name: str = "MintDeleteRecordTool"
    description: str = """General Tool to delete records in MintHCM modules, for example employees, candidates, meetings etc.
    Dont use this tool without knowing the fields available in the module. Use MintGetModuleFieldsTool to get list of fields available in the module.
    Use MintSearchTool to retrieve ID of the record"""
    args_schema: Type[BaseModel] = MintDeleteDataInput

    def _run(
        self,
        module_name: str,
        id: str,
        config: RunnableConfig,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        try:
            suitecrm = self.get_connection(config)
            url = f"{self.api_url}/module/{module_name}/{id}"
            response = suitecrm.request(url, "delete")
            return "W module " + module_name + " usunięto rekord o id: " + id
        except Exception as e:
            print(traceback.format_exc())
            raise ToolException(f"Error: {e}")
