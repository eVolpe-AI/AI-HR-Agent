from typing import Type, Optional, Any, Dict, List
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from langchain_core.tools import ToolException
from tools.MintHCM.BaseTool import MintBaseTool
from tools.MintHCM.SuiteAPI import SuiteCRM, Module

class MintGetModuleFieldsInput(BaseModel):
    module_name: str = Field(..., description="Name of the module in Mint in which the information is to be read")

class MintGetModuleFieldsTool(BaseTool, MintBaseTool):
    name: str = "MintGetModuleFieldsTool"
    description: str = """
    Tool to retrieve list of fields and their types in a MintHCM module. 
    Use This tool ALWAYS before using MintSearchTool to get list of fields available in the module.
    """
    args_schema: Type[BaseModel] = MintGetModuleFieldsInput

    def _run(self, module_name: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> Dict[str, Any]:
        try:
            suitecrm = self.get_connection()
            module = Module(suitecrm, module_name)
            fields = module.fields()
            return {"fields": fields}
        except Exception as e:
            raise ToolException(f"Error: {e}")
