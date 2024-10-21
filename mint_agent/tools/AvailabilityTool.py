import os
from enum import Enum
from typing import Type

import mysql.connector
from dotenv import load_dotenv
from langchain.tools import BaseTool
from langchain_core.runnables.config import RunnableConfig
from mysql.connector import Error
from pydantic import BaseModel, Field

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


class AvailabilityTool(BaseTool):
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
            return "Couldn't connect to the database. can't get the availability"

        meetings, calls = None, None
        mint_user_id = config.get("configurable", {}).get("mint_user_id")

        start_date_with_time = start_date + " 00:00:00"
        end_date_with_time = end_date + " 23:59:59"

        try:
            cursor = connection.cursor()
            if "meetings" in modules:
                cursor.execute(
                    """SELECT name, date_start, date_end 
                        FROM meetings 
                        WHERE id IN (SELECT meeting_id FROM meetings_users where user_id = %s) 
                        AND date_start >= %s
                        AND date_end <= %s""",
                    (mint_user_id, start_date_with_time, end_date_with_time),
                )
                meetings = cursor.fetchall()

            if "calls" in modules:
                cursor.execute(
                    """SELECT name, duration_hours, duration_minutes, date_start, date_end 
                        FROM calls 
                        WHERE id IN (SELECT call_id FROM calls_users WHERE user_id = %s)
                        AND date_start >= %s
                        AND date_end <= %s""",
                    (mint_user_id, start_date_with_time, end_date_with_time),
                )
                calls = cursor.fetchall()
            cursor.close()
        except Error as e:
            return f"Error while fetching data from database: {e}"

        if not meetings and not calls:
            return "No meetings or calls found in the given period"

        meetings_output = []
        for meeting in meetings:
            meetings_output.append(
                f"{meeting[0]}: {meeting[1].strftime('%Y-%m-%d %H:%M')} - {meeting[2].strftime('%Y-%m-%d %H:%M')}"
            )

        calls_output = []
        for call in calls:
            calls_output.append(
                f"{call[0]}: {call[3].strftime('%Y-%m-%d %H:%M')} - {call[4].strftime('%Y-%m-%d %H:%M')}"
            )

        if not meetings:
            return f"Calls: {calls_output}"
        if not calls:
            return f"Meetings: {meetings_output}"

        return f"Meetings: {meetings_output}. Calls: {calls_output}."
