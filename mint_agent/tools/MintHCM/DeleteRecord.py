from typing import Any, Dict, Optional, Type

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field

from mint_agent.tools.MintHCM.BaseTool import MintBaseTool


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
            suitecrm.request(url, "delete")
            return f"Record with id: {id} has been deleted from module {module_name}"
        except Exception as e:
            raise ToolException(f"Error: {e}")
