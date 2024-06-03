from langchain.pydantic_v1 import BaseModel, Field
from typing import Optional, Type
from langchain.tools import BaseTool
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from datetime import date


class CalendarInput(BaseModel):
    format: str = Field(description=" Date format to be returned. Default is YYYY-MM-DD (Day)")

class CalendarTool(BaseTool):
    name = "CalendarTool"
    description = "Useful for when you need to know current date. Input should be a date format. Always use this tool to get the current date if you are asked questions regarding today, yesterday, tommorow etc."
    args_schema: Type[BaseModel] = CalendarInput
    #return_direct: bool = True

    def _run(
        self, format: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        print("Calling CalendarTool._run()" + date.today().strftime("%Y-%m-%d (%A)"))
        return date.today().strftime("%Y-%m-%d (%A)")

    async def _arun(
        self,
        format: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""
        print("Calling CalendarTool._arun()" + date.today())
        raise NotImplementedError("Calendar does not support async")
