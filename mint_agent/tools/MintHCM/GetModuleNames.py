from typing import Any, Dict, List

from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import BaseTool, ToolException

from mint_agent.tools.MintHCM.BaseTool import MintBaseTool, tool_response


class MintGetModuleNamesTool(BaseTool, MintBaseTool):
    name: str = "MintGetModuleNamesTool"
    description: str = """
    Tool to retrieve list of module names. Use this tool only if user asks for list of available modules or to check if specific module exists
    """

    module_blacklist: List[str] = []
    use_blacklist: bool = False

    module_whitelist: List[str] = [
        "Meetings",
        "Tasks",
        "Certificates",
        "Responsibilities",
        "Calls",
        "Candidates",
        "Candidatures",
        "Benefits",
    ]
    use_whitelist: bool = True

    def _run(
        self,
        config: RunnableConfig,
    ) -> Dict[str, Any]:
        try:
            suitecrm = self.get_connection(config)
            modules = suitecrm.get_modules()

            if self.use_blacklist:
                modules = [
                    module for module in modules if module not in self.module_blacklist
                ]

            if self.use_whitelist:
                modules = [
                    module for module in modules if module in self.module_whitelist
                ]

            return tool_response(modules)
        except Exception as e:
            raise ToolException(f"Error: {e}")
