import json
from typing import Any, Dict, Optional, Type

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field

from mint_agent.tools.MintHCM.BaseTool import MintBaseTool, tool_response
from mint_agent.tools.MintHCM.GetModuleFields import MintGetModuleFieldsTool
from mint_agent.tools.MintHCM.GetModuleNames import MintGetModuleNamesTool
from mint_agent.tools.MintHCM.SuiteAPI import Module


class MintSearchInput(BaseModel):
    module_name: str = Field(
        ...,
        description="Name of the module in Mint in which the information is to be read",
    )
    filters: str = Field(
        ...,
        description="""
        JSON  with filters to apply to the query.
        Example:  { "filters": {

                         "date_start": { "operator": ">", "value": "2022-01-01" },
                         "assigned_user_id": { "operator": "=", "value": "1" }
                } }
        ONLY available operators : =, <> , > , >=,  < ,  <=, LIKE, NOT LIKE, IN, NOT IN, BETWEEN
        For operators IN, NOT IN set value as string with comma separated values.
        For operator BETWEEN set value as string with two values separated by comma.
        When performing search on a datetime field to find records related to a specific date, use operator BETWEEN  specific_date and specific_date + 1 day.
        Make sure to use operator BETWEEN for datetime fields when searching by datetime field to find records related to a specific date.
        Example, search for date_start on 2022-01-01:  { "filters": {
                         "date_start": { "operator": "BETWEEN", "value": "2022-01-01,2022-01-02" },
                } }
        Remember that dates returned by MintHCM are in UTC timezone.
        If you need BETWEEN operator, you need to use two filters with > and < operators.
    """,
    )
    operator: str = Field(
        ...,
        description="Operator to use to join all filters. Possible values: 'and','or'",
    )
    fields: str = Field(
        ...,
        description="List of fields to retrieve from the module. Example: 'id,name,date_start,status'. Always use MintGetModuleFieldsTool to get list of fields available in the module. Do not use this tool without knowing the fields available in the module!",
    )


class MintSearchTool(BaseTool, MintBaseTool):
    name: str = "MintSearchTool"
    description: str = "Tool to retrieve list of records from MintHCM. Always use MintGetModuleFieldsTool to get list of fields available in the module. Do not use this tool without knowing the fields available in the module!"
    args_schema: Type[BaseModel] = MintSearchInput

    def _run(
        self,
        module_name: str,
        filters: str,
        operator: str,
        fields: str,
        config: RunnableConfig,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        try:
            module_names = MintGetModuleNamesTool()._run(config=config)["response"]
            if module_name not in module_names:
                raise ToolException(
                    f"Module {module_name} does not exist. Try to use MintGetModuleNamesTool to get list of available modules."
                )

            module_fields = MintGetModuleFieldsTool()._run(module_name, config=config)[
                "response"
            ]["fields"]

            print(module_fields)

            fields_array = fields.replace(" ", "").split(",")
            available_fields = module_fields.keys()

            for field in fields_array:
                if field and field not in available_fields:
                    raise ToolException(
                        f"Field {field} is not available in the {module_name} module. Use MintGetModuleFieldsTool to get list of fields available in the module."
                    )

            suitecrm = self.get_connection(config)
            module = Module(suitecrm, module_name)

            filters_array = json.loads(filters)
            operator = operator if operator in ["and", "or"] else "and"

            if "filters" in filters_array:
                filter_fields = filters_array.get("filters", {})

                for field in filter_fields:
                    if field not in available_fields:
                        raise ToolException(
                            f"Field {field} is not available in the {module_name} module. Use MintGetModuleFieldsTool to get list of fields available in the module."
                        )
                response = module.get(
                    fields=fields_array,
                    sort=None,
                    operator=operator,
                    **filter_fields,
                )
            else:
                response = module.get(
                    fields=fields_array, sort=None, operator=operator, deleted="0"
                )

            return_data = [{"id": row["id"], **row["attributes"]} for row in response]

            if not return_data:
                return tool_response(
                    f"No records found in module {module_name} with given filters"
                )

            return tool_response(return_data)
        except Exception as e:
            raise ToolException(f"Error: {e}")
