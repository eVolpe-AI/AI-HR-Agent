from typing import Any, Dict, Optional, Type

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from mint_agent.tools.MintHCM.BaseTool import MintBaseTool, tool_response
from mint_agent.tools.MintHCM.SuiteAPI import Module


class MintGetRelInput(BaseModel):
    record_id: str = Field(
        ..., description="ID of the record to get relationships from"
    )
    base_module: str = Field(
        ..., description="Name of the module in which the record is present"
    )
    related_module: str = Field(..., description="Name of the related module")


class MintGetRelTool(BaseTool, MintBaseTool):
    name: str = "MintGetRelTool"
    description: str = "Tool to get relationships between records in MintHCM modules"
    args_schema: Type[BaseModel] = MintGetRelInput

    def _run(
        self,
        record_id: str,
        base_module: str,
        related_module: str,
        config: RunnableConfig,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        try:
            suitecrm = self.get_connection(config)
            module = Module(suitecrm, base_module)
            result = module.get_relationship(related_module, record_id)
            return tool_response(result)
        except Exception as e:
            return {"status": "error", "message": str(e)}
