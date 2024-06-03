from typing import Type, Optional, Any, Dict, List
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from langchain_core.tools import ToolException
from tools.MintHCM.BaseTool import MintBaseTool
from tools.MintHCM.SuiteAPI import SuiteCRM, Module


class MintGetUsersTool(BaseTool,MintBaseTool):
    name: str = "MintGetUsersTool"
    description: str = "Tool to retrieve list of users in MintHCM. Use this to get user id to assign records to users or add users to meetings."

    def _run(self, query_params: Optional[Dict[str, Any]] = None, run_manager: Optional[CallbackManagerForToolRun] = None) -> Dict[str, Any]:
        #suitecrm = MintConnection.get_connection()
        #url = f'{api_url}/meta/modules'
        #response = suitecrm.request(url, 'get', parameters=query_params)
        #data = response.get('data', [])
        #TODO nie działa po API?
        return [
            {
                "id": "1",
                "first_name": "",
                "last_name": "Administrator",
                "username": "admin",
                "email": "admin@example.com"
            },
            {
                "id": "f39a04c4-e537-4030-9d5a-6638bb2bb87d",
                "first_name": "Adam",
                "last_name": "Kowalski",
                "username": "kowalskim",
                "email": "kowalskim@example.com"
            },
            {
                "id": "ad3b421f-a6de-4566-c4d5-6638bc48d1c3",
                "first_name": "Anna",
                "last_name": "Wiśniewska",
                "username": "wisniewska",
                "email": "wisniewska@example.com"
            }
        ]