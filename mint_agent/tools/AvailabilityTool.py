import os
from enum import Enum
from typing import Type

import mysql.connector
from dotenv import load_dotenv
from langchain.tools import BaseTool
from langchain_core.runnables.config import RunnableConfig
from mysql.connector import Error
from pydantic import BaseModel, Field

from mint_agent.tools.MintHCM.BaseTool import ToolUtils, tool_response

load_dotenv()


class ModuleType(str, Enum):
    MEETINGS = "meetings"
    CALLS = "calls"


class AvailabilityInput(BaseModel):
    start_date: str = Field(description="Start date of the period in YYYY-MM-DD format")
    end_date: str = Field(description="End date of the period in YYYY-MM-DD format")
    modules: list[ModuleType] = Field(
        description="List of modules to check availability for, can include 'meetings' and/or 'calls'"
    )


class AvailabilityTool(BaseTool, ToolUtils):
    name: str = "AvailabilityTool"
    description: str = """
        Useful when you want to check the availability of a person. This tool returns information about times when user is not available due to meetings and/or calls. 
    """
    args_schema: Type[BaseModel] = AvailabilityInput

    def _run(
        self,
        config: RunnableConfig,
        start_date: str,
        end_date: str,
        modules: list[ModuleType],
    ) -> str:
        """Use the tool."""
        try:
            connection = mysql.connector.connect(
                host=os.environ.get("MINTDB_URI"),
                user=os.environ.get("MINTDB_USER"),
                password=os.environ.get("MINTDB_PASS"),
                port=os.environ.get("MINTDB_PORT"),
                database=os.environ.get("MINTDB_DATABASE_NAME"),
            )
        except Error:
            return tool_response(
                "Couldn't connect to the database. Can't get the availability"
            )

        meetings_output, calls_output = [], []  # Initialize outputs as empty lists

        mint_user_id = config.get("configurable", {}).get("mint_user_id")
        start_date_with_time = f"{start_date} 00:00:00"
        end_date_with_time = f"{end_date} 23:59:59"

        try:
            cursor = connection.cursor()
            if "meetings" in modules:
                cursor.execute(
                    """SELECT name, date_start, date_end 
                    FROM meetings 
                    WHERE id IN (SELECT meeting_id FROM meetings_users WHERE user_id = %s) 
                    AND date_start >= %s
                    AND date_end <= %s""",
                    (mint_user_id, start_date_with_time, end_date_with_time),
                )
                meetings_output = [
                    f"{m[0]}: {m[1].strftime('%Y-%m-%d %H:%M')} - {m[2].strftime('%Y-%m-%d %H:%M')}"
                    for m in cursor.fetchall()
                ]

            if "calls" in modules:
                cursor.execute(
                    """SELECT name, duration_hours, duration_minutes, date_start, date_end 
                    FROM calls 
                    WHERE id IN (SELECT call_id FROM calls_users WHERE user_id = %s)
                    AND date_start >= %s
                    AND date_end <= %s""",
                    (mint_user_id, start_date_with_time, end_date_with_time),
                )
                calls_output = [
                    f"{c[0]}: {c[3].strftime('%Y-%m-%d %H:%M')} - {c[4].strftime('%Y-%m-%d %H:%M')}"
                    for c in cursor.fetchall()
                ]
            cursor.close()
        except Error as e:
            return tool_response(f"Error while fetching data from database: {e}")

        if meetings_output and calls_output:
            return tool_response(f"Meetings: {meetings_output}. Calls: {calls_output}.")
        elif meetings_output:
            return tool_response(f"Meetings: {meetings_output}.")
        elif calls_output:
            return tool_response(f"Calls: {calls_output}.")
        else:
            return tool_response("No records found")
