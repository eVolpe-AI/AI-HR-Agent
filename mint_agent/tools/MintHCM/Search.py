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
        description="Operator to use to join all filter. Possible values: 'and','or'",
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
            module_names_tool = MintGetModuleNamesTool()
            module_names = module_names_tool._run(config=config)

            if module_name not in module_names:
                raise ToolException(
                    f"Module {module_name} does not exist. Try to use MintGetModuleNamesTool to get list of available modules."
                )

            module_fields_tool = MintGetModuleFieldsTool()

            module_fields = module_fields_tool._run(module_name, config=config)
            # we need to check if the fields provided in the fields argument are in the module_fields
            # Example module_fields:
            # {'fields': {'id': {'dbType': 'id'}, 'name': {'dbType': 'name'}, 'date_entered': {'dbType': 'datetime'}}
            fields_array = fields.replace(" ", "").split(",")
            fieldss = module_fields["fields"]
            field_names = fieldss.keys()
            for field in fields_array:
                if field and field not in field_names:
                    # print(f"Field {field} is not available in the module {module_name}. Use MintGetModuleFieldsTool to get list of fields available in the module.")
                    # print(field_names)
                    raise ToolException(
                        f"Field {field} is not available in the module {module_name}. Use MintGetModuleFieldsTool to get list of fields available in the module."
                    )

            suitecrm = self.get_connection(config)
            module = Module(suitecrm, module_name)

            # print(f"Module: {module_name}, filters: {filters}, fields: {fields}")

            filters_array = json.loads(filters)
            fields_array = fields.replace(" ", "").split(",")

            # print(f"Filters: {filters_array}")
            # print(f"Fields: {fields_array}")

            if operator not in ["and", "or"]:
                operator = "and"
            operators = {
                "=": "EQ",
                "<>": "NEQ",
                ">": "GT",
                ">=": "GTE",
                "<": "LT",
                "<=": "LTE",
            }

            if "filters" in filters_array:
                filter_list_filters = filters_array["filters"]

                print(f"filter_list_filters: {filter_list_filters}")
                #    filter_str = ""
                # for f in filter_list_filters:
                #    print(f'fff: {f}')
                #     for key in f:
                #         filter_str += f"{key} {f[key]['operator']} '{f[key]['value']}' AND "

                if filter_list_filters:
                    # we need to check if the fields provided in the filters are in the module_fields
                    for field, value in filter_list_filters.items():
                        if field and field not in field_names:
                            # print(f"Field {field} is not available in the module {module_name}. Use MintGetModuleFieldsTool to get list of fields available in the module.")
                            print(module_fields)

                            raise ToolException(
                                f"Field {field} is not available in the module {module_name}. Use MintGetModuleFieldsTool to get list of fields available in the module."
                            )

                    #        for field, value in filter_list_filters.items():
                    #            print(f'fff: {field}, {value}')
                    #            if isinstance(value, dict):
                    #                filter_str = f'{filter_str}[{field}][{operators[value["operator"]]}]={value["value"]}and&'
                    #            else:
                    #                filter_str = f'{filter_str}[{field}][eq]={value}and&'
                    #        print(f'Filters string : {filter_str}')

                    # filter_list_filters.operator = 'AND'
                    response = module.get(
                        fields=fields_array,
                        sort=None,
                        operator=operator,
                        **filter_list_filters,
                    )
                else:
                    response = module.get(
                        fields=fields_array, sort=None, operator=operator, deleted="0"
                    )
            else:
                response = module.get(
                    fields=fields_array, sort=None, operator=operator, deleted="0"
                )
            print(f"response: {response}")
            data = response
            # copy rows from data to return_data, only the attributes
            return_data = []
            for row in data:
                return_data.append({"id": row["id"], **row["attributes"]})
            return tool_response({"data": return_data})
        except Exception as e:
            raise ToolException(f"Error: {e}")
