from datetime import date
from typing import Optional, Type

from langchain.callbacks.manager import (
    CallbackManagerForToolRun,
)
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool


class CalendarInput(BaseModel):
    format: str = Field(
        description=" Date format to be returned. Default is YYYY-MM-DD (Day)"
    )


class CalendarTool(BaseTool):
    name = "CalendarTool"
    description = "Useful for when you need to know current date. Input should be a date format. Always use this tool to get the current date if you are asked questions regarding today, yesterday, tomorrow etc."
    args_schema: Type[BaseModel] = CalendarInput
    # return_direct: bool = True

    def _run(
        self, format: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        return date.today().strftime("%Y-%m-%d (%A)")
