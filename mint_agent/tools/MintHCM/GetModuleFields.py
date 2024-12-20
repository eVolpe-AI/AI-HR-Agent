from typing import Any, Dict, Optional, Type

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field

from mint_agent.tools.MintHCM.BaseTool import MintBaseTool
from mint_agent.tools.MintHCM.SuiteAPI import Module


class MintGetModuleFieldsInput(BaseModel):
    module_name: str = Field(
        ...,
        description="Name of the module in Mint in which the information is to be read",
    )


class MintGetModuleFieldsTool(BaseTool, MintBaseTool):
    name: str = "MintGetModuleFieldsTool"
    description: str = """
    Tool to retrieve list of fields and their types in a MintHCM module. 
    Use This tool ALWAYS before using MintSearchTool to get list of fields available in the module.
    """
    args_schema: Type[BaseModel] = MintGetModuleFieldsInput

    def _run(
        self,
        module_name: str,
        config: RunnableConfig,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        try:
            suitecrm = self.get_connection(config)
            module = Module(suitecrm, module_name)
            fields = module.fields()
            return {"fields": fields}
        except Exception as e:
            raise ToolException(f"Error: {e}")
