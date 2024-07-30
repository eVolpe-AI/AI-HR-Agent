import traceback

from langchain_core.tools import ToolException

from tools.CalendarTool import CalendarTool
from tools.MintHCM.CreateMeeting import MintCreateMeetingTool
from tools.MintHCM.CreateRecord import MintCreateRecordTool
from tools.MintHCM.GetModuleFields import MintGetModuleFieldsTool
from tools.MintHCM.GetModuleNames import MintGetModuleNamesTool
from tools.MintHCM.GetUsers import MintGetUsersTool
from tools.MintHCM.Search import MintSearchTool


def _handle_tool_error(error: ToolException) -> str:
    # find if what was returned contains fraze "Module ... does not exist"
    print("FULL TRACEBACK:")
    print(traceback.format_exc())
    if "does not exist" in error.args[0]:
        return f"Module Error: {error} . Try to use MintGetModuleNamesTool to get list of available modules."
    else:
        return (
            "The following errors occurred during tool execution:"
            + error.args[0]
            + "Please try another tool."
        )


class ToolController:
    available_tools = {
        "MintGetModuleNamesTool": MintGetModuleNamesTool(
            handle_tool_error=_handle_tool_error
        ),
        "MintGetModuleFieldsTool": MintGetModuleFieldsTool(
            handle_tool_error=_handle_tool_error
        ),
        "MintSearchTool": MintSearchTool(handle_tool_error=_handle_tool_error),
        "MintCreateRecordTool": MintCreateRecordTool(
            handle_tool_error=_handle_tool_error
        ),
        "MintCreateMeetingTool": MintCreateMeetingTool(
            handle_tool_error=_handle_tool_error
        ),
        "MintGetUsersTool": MintGetUsersTool(handle_tool_error=_handle_tool_error),
        # "Search": DuckDuckGoSearchResults(name="Search"),
        "CalendarTool": CalendarTool(name="CalendarTool"),
    }

    default_tools = [
        # "MintGetModuleNamesTool",
        # "MintGetModuleFieldsTool",
        # "MintCreateRecordTool",
        # "MintCreateMeetingTool",
        # "MintSearchTool",
        # "MintGetUsersTool",
        "CalendarTool",
    ]

    safe_tools = [
        # "CalendarTool",
    ]

    @staticmethod
    def get_available_tools():
        return ToolController.available_tools

    @staticmethod
    def get_default_tools():
        return ToolController.default_tools

    @staticmethod
    def get_safe_tools():
        return ToolController.safe_tools
