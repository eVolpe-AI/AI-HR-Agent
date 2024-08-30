from datetime import date
from typing import Optional, Type

import mysql.connector
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool
from langchain_core.runnables.config import RunnableConfig
from mysql.connector import Error


class AvailibilityInput(BaseModel):
    current_user_id: str = Field(
        description="ID of the user for whom you want to check the availibility"
    )
    start_date: str = Field(description="Start date of the period in YYYY-MM-DD format")
    end_date: str = Field(description="End date of the period in YYYY-MM-DD format")


class AvailibilityTool(BaseTool):
    name = "AvailibilityTool"
    description = """
        Useful when you want to check the availibility of a person. This tool returns infromation about times when user is not available due to meetings, appointments etc. 
    """
    args_schema: Type[BaseModel] = AvailibilityInput

    def _run(
        self,
        config: RunnableConfig,
        current_user_id: str,
        start_date: str,
        end_date: str,
    ) -> str:
        """Use the tool."""
        print(f"current_user_id: {current_user_id}")
        try:
            connection = mysql.connector.connect(
                host="voicebot.int1.evolpe.net",
                user="root",
                password="t4jn3h4slo",
                port="3537",
                database="minthcm",
            )
        except Error:
            return f"Coudn't connect to the database. can't get the availibility"

        try:
            cursor = connection.cursor()
            cursor.execute(
                """SELECT name, date_start, date_end 
                FROM meetings 
                WHERE id IN (
                    SELECT meeting_id FROM meetings_users where user_id = 1
                ) AND date_start >= %s
                AND date_end <= %s""",
                (start_date, end_date),
            )
            meetings = cursor.fetchall()
            cursor.close()
        except Error as e:
            return f"Error while fetching data from database: {e}"

        meetings_table = []
        meetings_table.append("__TABLE__")
        for meeting in meetings:
            meetings_table.append(f"{meeting[0]}-{meeting[1]}-{meeting[2]}")
        meetings_table.append("__END_TABLE__")
        return "\n".join(meetings_table)
