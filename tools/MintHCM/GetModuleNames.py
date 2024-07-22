from typing import Any, Dict, List, Optional, Type

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field

from tools.MintHCM.BaseTool import MintBaseTool
from tools.MintHCM.SuiteAPI import Module, SuiteCRM


class MintGetModuleNamesTool(BaseTool, MintBaseTool):
    name: str = "MintGetModuleNamesTool"
    description: str = """
    Tool to retrieve list of module names. Use this tool only if user asks for list of avaliable modules or to check if specific module exists"""

    def _run(
        self,
        query_params: Optional[Dict[str, Any]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        # suitecrm = MintConnection.get_connection()
        # url = f'{api_url}/meta/modules'
        # response = suitecrm.request(url, 'get', parameters=query_params)
        # data = response.get('data', [])
        # TODO implement this method
        return """
        Available modules in MintHCM:
        - Candidates
        - Meetings
        - Tasks
        - Candidatures
        """
