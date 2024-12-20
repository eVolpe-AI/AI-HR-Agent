from typing import Any, Dict, Optional, Type

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field

from mint_agent.tools.MintHCM.BaseTool import MintBaseTool


class MintCreateDataInput(BaseModel):
    module_name: str = Field(
        ...,
        description="Name of the module in Mint in which the record is to be created",
    )
    attributes: Dict[str, Any] = Field(
        ..., description="Record attributes in key-value format"
    )


class MintCreateRecordTool(BaseTool, MintBaseTool):
    name: str = "MintCreateRecordTool"
    description: str = """General Tool to create new record in MintHCM modules, for example  new employees, new candidates etc.
    Dont use this tool for meetings. Use MintCreateMeetingTool for meetings.
    Dont use this tool without knowing the fields available in the module. Use MintGetModuleFieldsTool to get list of fields available in the module."""
    args_schema: Type[BaseModel] = MintCreateDataInput

    def _run(
        self,
        module_name: str,
        attributes: Dict[str, Any],
        config: RunnableConfig,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        try:
            suitecrm = self.get_connection(config)
            url = f"{self.api_url}/module"
            data = {"type": module_name, "attributes": attributes}
            suitecrm.request(url, "post", parameters=data)
            return f"New record created for module: {module_name}"
        except Exception as e:
            raise ToolException(f"Error: {e}")
