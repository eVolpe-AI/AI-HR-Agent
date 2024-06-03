from typing import Type, Optional, Any, Dict, List
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from langchain_core.tools import ToolException
from tools.MintHCM.BaseTool import MintBaseTool
import traceback

class MintCreateMeetingInput(BaseModel):
    module_name: str = Field(..., description="Name of the module in Mint in which the record is to be created")
    attributes: Dict[str, Any] = Field(..., description="""
    Record attributes in key-value format, value CAN NOT be a list.
    Example: { 'name': 'Meeting with John', 'date_start': '2022-01-01 12:00:00', 'date_end': '2022-01-01 13:00:00', 'assigned_user_id': '1'}
    """)
    attendees: List[str] = Field(..., description="""
    List of ids of attendees to the meeting. Example: ['1', 'f39a04c4-e537-4030-9d5a-6638bb2bb87d']
    If you have just first_name and a last_name or username use MintSearchTool to search for user id in MintHCM.
    """)

class MintCreateMeetingTool(BaseTool, MintBaseTool):
    name: str = "MintCreateMeetingTool"
    description: str ="""
    Tool to create new meetings with attendees in MintHCM modules.
    Dont use this tool without knowing the fields available in the module.
    Use CalendarTool to get current_date and derrive from it propoer date_start and date_end for the meeting if asked to create meeting for today, tommorow etc.
    Use MintGetModuleFieldsTool to get list of fields available in the module.
    """
    args_schema: Type[BaseModel] = MintCreateMeetingInput

    def _run(self, module_name: str, attributes: Dict[str, Any], attendees: List[str],
        run_manager: Optional[CallbackManagerForToolRun] = None) -> Dict[str, Any]:
        try:
            suitecrm = self.get_connection()
            url = f'{self.api_url}/module'
            data = {"type": module_name, "attributes": attributes}
            response = suitecrm.request(url, 'post', parameters=data)
            if attendees:
                for attendee in attendees:
                    url = f'{self.api_url}/module/{module_name}/{response["data"]["id"]}/relationships/users'
                    data = {"type": "Users", "id": attendee}
                    response2 = suitecrm.request(url, 'post', parameters=data)
            return response
        except Exception as e:
            print(traceback.format_exc())
            raise ToolException(f"Error: {e}")