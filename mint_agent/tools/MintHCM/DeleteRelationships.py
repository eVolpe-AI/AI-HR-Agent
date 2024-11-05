from typing import Any, Dict, Optional, Type

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from mint_agent.tools.MintHCM.BaseTool import MintBaseTool, ToolUtils, tool_response


class MintDeleteRelInput(BaseModel):
    record_id: str = Field(
        ..., description="ID of the record to delete a relationship from"
    )
    related_module: str = Field(..., description="Name of the related module")
    related_id: str = Field(..., description="ID of the related record")


class MintDeleteRelTool(BaseTool, MintBaseTool):
    name: str = "MintDeleteRelTool"
    description: str = """Tool to delete a relationship between records in MintHCM modules. If you don't know ID numbers, you need to get
    both record_id and related_id by using MintSearchTool"""
    args_schema: Type[BaseModel] = MintDeleteRelInput

    def _run(
        self,
        record_id: str,
        related_module: str,
        related_id: str,
        config: RunnableConfig,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        try:
            suitecrm = self.get_connection(config)
            result = suitecrm.Meetings.delete_relationship(
                record_id, related_module, related_id
            )
            return tool_response({"status": "success", "result": result})
        except Exception as e:
            return tool_response({"status": "error", "message": str(e)})
