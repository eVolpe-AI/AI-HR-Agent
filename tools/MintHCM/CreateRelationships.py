from typing import Type, Optional, Any, Dict
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_core.tools import ToolException
from tools.MintHCM.BaseTool import MintBaseTool

class MintCreateRelInput(BaseModel):
    record_id: str = Field(..., description="ID of the record to create a relationship from")
    related_module: str = Field(..., description="Name of the related module")
    related_id: str = Field(..., description="ID of the related record")

class MintCreateRelTool(BaseTool, MintBaseTool):
    name: str = "MintCreateRelTool"
    description: str = """Tool to create a relationship between records in MintHCM modules. Firstly, you need to get both record_id and related_id by
    using MintSearchTool"""
    args_schema: Type[BaseModel] = MintCreateRelInput

    def _run(self, record_id: str, related_module: str, related_id: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> Dict[str, Any]:
        try:
            suitecrm = self.get_connection()
            result = suitecrm.Meetings.create_relationship(record_id, related_module, related_id)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}
