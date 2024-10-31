from typing import Any, Dict, List, Optional, Type

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field

from mint_agent.tools.MintHCM.BaseTool import MintBaseTool
from mint_agent.tools.MintHCM.SuiteAPI import Module, SuiteCRM


class MintGetUsersTool(BaseTool, MintBaseTool):
    name: str = "MintGetUsersTool"
    description: str = "Tool to retrieve list of users in MintHCM. Use this to get list of users in MintHCM and their details such as id, name, phone numbers, email, adress etc."

    def _run(
        self,
        config: RunnableConfig,
        query_params: Optional[Dict[str, Any]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        try:
            suitecrm = self.get_connection(config)
            module = Module(suitecrm, "Users")
            api_response = module.get_all()

            users = []
            for user in api_response["data"]:
                user_id = user["id"]
                attributes = user["attributes"]

                name = attributes.get("full_name", "")

                phone_home = attributes.get("phone_home", "")
                phone_mobile = attributes.get("phone_mobile", "")
                phone_work = attributes.get("phone_work", "")
                phone_other = attributes.get("phone_other", "")

                address_street = attributes.get("address_street", "")
                address_city = attributes.get("address_city", "")
                address_state = attributes.get("address_state", "")
                address_country = attributes.get("address_country", "")
                address_postalcode = attributes.get("address_postalcode", "")

                user_type = attributes.get("UserType", "")
                employee_status = attributes.get("employee_status", "")

                email_address = attributes.get("email_addresses_primary", "")

                position = attributes.get("position_name", "")
                reports_to_id = attributes.get("reports_to_id", "")

                user_data = f"""ID: {user_id}, Name and surname: {name}, id of supervisor: {reports_to_id}
                Home phone: {phone_home}, Mobile phone: {phone_mobile}, Work phone: {phone_work}, Other phone: {phone_other}, Email: {email_address},
                Address: (street: {address_street}, city: {address_city}, state: {address_state}, country: {address_country}, postal code: {address_postalcode}),
                User type: {user_type},
                Employee status: {employee_status},
                Position: {position},
                """
                users.append(user_data)
            return users

        except Exception as e:
            return f"While trying to get users, an error occurred: {e}"
