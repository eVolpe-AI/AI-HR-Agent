from datetime import date
from typing import Optional, Type

from langchain.callbacks.manager import (
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from mint_agent.tools.MintHCM.BaseTool import tool_response


class CalendarInput(BaseModel):
    format: str = Field(
        description=" Date format to be returned. Default is YYYY-MM-DD (Day)"
    )


class CalendarTool(BaseTool):
    name: str = "CalendarTool"
    description: str = "Useful for when you need to know current date. Input should be a date format. Always use this tool to get the current date if you are asked questions regarding today, yesterday, tomorrow etc."
    args_schema: Type[BaseModel] = CalendarInput
    # return_direct: bool = True

    def _run(
        self, format: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> dict:
        """Use the tool."""
        return tool_response(date.today().strftime("%Y-%m-%d (%A)"))

    def get_request_info():
        return {"format": "Date format to be returned"}
