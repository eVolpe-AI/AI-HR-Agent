from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field

from mint_agent.database.mint_db import to_db_time
from mint_agent.tools.MintHCM.BaseTool import (
    MintBaseTool,
    ToolFieldDescription,
    tool_response,
)


class MintCreateMeetingInput(BaseModel):
    attributes: Dict[str, Any] = Field(
        ...,
        description="""
    Record attributes in key-value format, value CAN NOT be a list.
    Example: { 'name': 'Meeting with John', 'date_start': '2022-01-01 12:00:00', 'date_end': '2022-01-01 13:00:00', 'assigned_user_id': '1'}
    """,
        json_schema_extra={
            "field_description": ToolFieldDescription(
                {
                    "name": ToolFieldDescription("Meeting name", required=True),
                    "date_start": ToolFieldDescription("Start time", required=True),
                    "date_end": ToolFieldDescription("End time", required=True),
                    "assigned_user_id": ToolFieldDescription(
                        "Assigned to",
                        "link",
                        module="Users",
                        required=True,
                    ),
                },
                "dict",
            ),
        },
    )
    attendees: List[str] = Field(
        ...,
        description="""
    List of ids of attendees to the meeting. Example: ['1', 'f39a04c4-e537-4030-9d5a-6638bb2bb87d']
    If you have just first_name and a last_name or username use MintSearchTool to search for user id in MintHCM. 
    """,
        json_schema_extra={
            "field_description": ToolFieldDescription(
                "Attendees", "link_array", module="Users"
            ),
        },
    )
    candidates: List[str] = Field(
        ...,
        description="""
    List of ids of candidates to the meeting. Example: ['26c2081a-1f55-66f7-7b49-6662ef7ab388','68339282-a9f3-ed1d-7ffe-662f6fadd1a9']
    If you have just first_name and a last_name of the candidate, use MintSearchTool to search for candidate id in MintHCM.
    """,
        json_schema_extra={
            "field_description": ToolFieldDescription(
                "Candidates", "link_array", module="Candidates"
            )
        },
    )


class MintCreateMeetingTool(BaseTool, MintBaseTool):
    name: str = "MintCreateMeetingTool"
    description: str = """
    Tool to create new meetings with attendees in MintHCM modules.
    Dont use this tool without knowing the fields available in the module.
    Use CalendarTool to get current_date and derive from it proper date_start and date_end for the meeting if asked to create meeting for today, tomorrow etc.
    Use MintGetModuleFieldsTool to get list of fields available in the module.
    """
    request_message: str = "Agent wants to create a meeting"
    args_schema: Type[BaseModel] = MintCreateMeetingInput

    def _run(
        self,
        attributes: Dict[str, Any],
        attendees: List[str],
        candidates: Optional[List[str]],
        config: RunnableConfig,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        meeting_start_date = attributes.get("date_start")
        meeting_end_date = attributes.get("date_end")

        date_format = "%Y-%m-%d %H:%M:%S"

        try:
            start_date = datetime.strptime(meeting_start_date, date_format)
            end_date = datetime.strptime(meeting_end_date, date_format)
        except ValueError:
            raise ToolException(
                "date_start and date_end must be in format 'YYYY-MM-DD HH:MM:SS' e.g. '2022-01-01 12:00:00'"
            )

        attributes["duration_hours"] = (end_date - start_date).seconds // 3600
        attributes["duration_minutes"] = (end_date - start_date).seconds % 3600 // 60

        attributes["date_start"] = to_db_time(meeting_start_date, date_format)
        attributes["date_end"] = to_db_time(meeting_end_date, date_format)

        current_user_id = config["configurable"]["mint_user_id"]

        try:
            module_name = "Meetings"
            suitecrm = self.get_connection(config)

            for attendee in attendees:
                if not suitecrm.verify_record_exists(attendee, "Users"):
                    return tool_response(f"User with id {attendee} does not exist")

            if current_user_id not in attendees:
                attendees.append(current_user_id)

            for candidate in candidates:
                if not suitecrm.verify_record_exists(candidate, "Candidates"):
                    return tool_response(
                        f"Candidate with id {candidate} does not exist"
                    )

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
