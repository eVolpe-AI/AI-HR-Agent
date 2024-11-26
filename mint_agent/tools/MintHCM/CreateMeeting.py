from typing import Any, Dict, List, Optional, Type

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field

from mint_agent.tools.MintHCM.BaseTool import MintBaseTool, tool_response
from mint_agent.tools.MintHCM.SuiteAPI import Module


class MintCreateMeetingInput(BaseModel):
    module_name: str = Field(
        ...,
        description="Name of the module in Mint in which the record is to be created",
    )
    attributes: Optional[Dict[str, Any]] = Field(
        ...,
        description="""
    Record attributes in key-value format, value CAN NOT be a list.
    Example: { 'name': 'Meeting with John', 'date_start': '2022-01-01 12:00:00', 'date_end': '2022-01-01 13:00:00', 'assigned_user_id': '1'}
    """,
    )
    attendees: List[str] = Field(
        ...,
        description="""
    List of ids of attendees to the meeting. Example: ['1', 'f39a04c4-e537-4030-9d5a-6638bb2bb87d']
    If you have just first_name and a last_name or username use MintSearchTool to search for user id in MintHCM.
    """,
    )
    candidates: List[str] = Field(
        ...,
        description="""
    List of ids of candidates to the meeting. Example: ['26c2081a-1f55-66f7-7b49-6662ef7ab388','68339282-a9f3-ed1d-7ffe-662f6fadd1a9']
    If you have just first_name and a last_name of the candidate, use MintSearchTool to search for candidate id in MintHCM.
    """,
    )


class MintCreateMeetingTool(BaseTool, MintBaseTool):
    name: str = "MintCreateMeetingTool"
    description: str = """
    Tool to create new meetings with attendees in MintHCM modules.
    Dont use this tool without knowing the fields available in the module.
    Use CalendarTool to get current_date and derive from it proper date_start and date_end for the meeting if asked to create meeting for today, tomorrow etc.
    Use MintGetModuleFieldsTool to get list of fields available in the module.
    """
    args_schema: Type[BaseModel] = MintCreateMeetingInput

    def _run(
        self,
        module_name: str,
        attributes: Dict[str, Any],
        attendees: List[str],
        candidates: Optional[List[str]],
        config: RunnableConfig,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        try:
            suitecrm = self.get_connection(config)
            url = f"{self.api_url}/module"
            data = {"type": module_name, "attributes": attributes}
            response = suitecrm.request(url, "post", parameters=data)
            meeting_url = suitecrm.get_record_url(module_name, response["data"]["id"])

            def add_relationships(relationship_type, ids):
                for record_id in ids:
                    relationship_url = f'{self.api_url}/module/{module_name}/{response["data"]["id"]}/relationships/{relationship_type}'
                    relationship_data = {
                        "type": relationship_type.capitalize(),
                        "id": record_id,
                    }
                    suitecrm.request(
                        relationship_url, "post", parameters=relationship_data
                    )

            if attendees:
                add_relationships("users", attendees)
            if candidates:
                add_relationships("candidates", candidates)

            return tool_response(
                "New meeting created in module 'Meetings'", {"url": meeting_url}
            )

        except Exception as e:
            raise ToolException(f"Error: {e}")
