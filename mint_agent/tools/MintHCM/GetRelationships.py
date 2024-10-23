from typing import Any, Dict, Optional, Type

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from mint_agent.tools.MintHCM.BaseTool import MintBaseTool


class MintGetRelInput(BaseModel):
    record_id: str = Field(
        ..., description="ID of the record to get relationships from"
    )
    related_module: str = Field(..., description="Name of the related module")


class MintGetRelTool(BaseTool, MintBaseTool):
    name: str = "MintGetRelTool"
    description: str = "Tool to get relationships between records in MintHCM modules"
    args_schema: Type[BaseModel] = MintGetRelInput

    def _run(
        self,
        record_id: str,
        related_module: str,
        config: RunnableConfig,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        try:
            suitecrm = self.get_connection(config)
            suitecrm.Meetings.get_relationship(record_id, related_module)
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
