from langchain_core.tools import ToolException
from loguru import logger

from mint_agent.tools.AvailabilityTool import AvailabilityTool
from mint_agent.tools.CalendarTool import CalendarTool
from mint_agent.tools.MintHCM.CreateMeeting import MintCreateMeetingTool
from mint_agent.tools.MintHCM.CreateRecord import MintCreateRecordTool
from mint_agent.tools.MintHCM.CreateRelationships import MintCreateRelTool
from mint_agent.tools.MintHCM.DeleteRecord import MintDeleteRecordTool
from mint_agent.tools.MintHCM.DeleteRelationships import MintDeleteRelTool
from mint_agent.tools.MintHCM.GetModuleFields import MintGetModuleFieldsTool
from mint_agent.tools.MintHCM.GetModuleNames import MintGetModuleNamesTool
from mint_agent.tools.MintHCM.GetRelationships import MintGetRelTool
from mint_agent.tools.MintHCM.GetUsers import MintGetUsersTool
from mint_agent.tools.MintHCM.Search import MintSearchTool
from mint_agent.tools.MintHCM.UpdateFields import MintUpdateFieldsTool


def _handle_tool_error(error: ToolException) -> str:
    # find if what was returned contains phrase "Module ... does not exist"
    if "does not exist" in error.args[0]:
        logger.error(f"Agent was trying to use module, which does not exist. {error}")
        return f"Module Error: {error} . Try to use MintGetModuleNamesTool to get list of available modules."
    else:
        logger.error(f"The following error occurred during tool execution: {error}")
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
        "UpdateFieldsTool": MintUpdateFieldsTool(handle_tool_error=_handle_tool_error),
        "MintCreateRelTool": MintCreateRelTool(handle_tool_error=_handle_tool_error),
        "MintDeleteRecordTool": MintDeleteRecordTool(
            handle_tool_error=_handle_tool_error
        ),
        "MintDeleteRelTool": MintDeleteRelTool(handle_tool_error=_handle_tool_error),
        "MintGetRelTool": MintGetRelTool(handle_tool_error=_handle_tool_error),
        "CalendarTool": CalendarTool(name="CalendarTool"),
        "AvailabilityTool": AvailabilityTool(),
    }

    default_tools = [
        "MintGetModuleNamesTool",
        "MintGetModuleFieldsTool",
        "MintSearchTool",
        "MintCreateRecordTool",
        "MintCreateMeetingTool",
        "MintGetUsersTool",
        "UpdateFieldsTool",
        "MintCreateRelTool",
        "MintDeleteRecordTool",
        "MintDeleteRelTool",
        "MintGetRelTool",
        "CalendarTool",
        "AvailabilityTool",
    ]

    safe_tools = [
        "CalendarTool",
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

    @staticmethod
    def get_tools():
        available_tools = ToolController.get_available_tools()
        default_tools = ToolController.get_default_tools()
        return [available_tools[tool] for tool in default_tools]
