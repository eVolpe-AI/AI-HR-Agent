from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun
from typing import Type, Optional, Any, Dict, List
from langchain_core.tools import ToolException
from tools.MintHCM.BaseTool import MintBaseTool
import traceback



class MintUpdateDataInput(BaseModel):
    module_name: str = Field(..., description="Name of the module in MintHCM system. If you don't know the module, use MintSearchTool to search for module name in MintHCM.")
    id: str = Field(..., description="ID number of the record to update. If you don't know id, use MintSearchTool to search for record id in MintHCM.")
    attributes: Dict[str, Any] = Field(..., description="Attributes to update in key-value format")

class MintUpdateFieldsTool(BaseTool, MintBaseTool):
    name = "MintUpdateFieldsTool"
    description = """Use this tool to update fields in the module based on data received from the user. Use this tool to update value of the field in the module,
    for example, duration or start date. Before using MintUpdateFieldsTool, ensure you have the correct module name and record ID. If not, use MintSearchTool to retrieve them.
"""
    args_schema: Type[BaseModel] = MintUpdateDataInput

    def _run(self, module_name: str, id: str, attributes: Dict[str, Any], run_manager: Optional[CallbackManagerForToolRun] = None) -> Dict[str, Any]:
        try:
            suitecrm = self.get_connection()
            url = f'{self.api_url}/module'
            data = {"type": module_name, "id": id, "attributes": attributes}
            response = suitecrm.request(url, 'patch', parameters=data)
            return "Zaktualizowano pole w module " + module_name + "o ID " + id
        
        except Exception as e:
            print(traceback.format_exc())
            raise ToolException(f"Error: {e}")
