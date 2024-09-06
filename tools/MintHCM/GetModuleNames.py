from typing import Any, Dict, List, Optional, Type

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field

from tools.MintHCM.BaseTool import MintBaseTool
from tools.MintHCM.SuiteAPI import Module, SuiteCRM


class MintGetModuleNamesTool(BaseTool, MintBaseTool):
    name: str = "MintGetModuleNamesTool"
    description: str = """
    Tool to retrieve list of module names. Use this tool only if user asks for list of avaliable modules or to check if specific module exists
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

            return modules
        except Exception as e:
            return f"Error occured while trying to get list of modules: {e}"
