from typing import Any, Dict, List, Optional, Type

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field

from tools.MintHCM.BaseTool import MintBaseTool
from tools.MintHCM.SuiteAPI import Module, SuiteCRM


class MintGetUsersTool(BaseTool, MintBaseTool):
    name: str = "MintGetUsersTool"
    description: str = (
        "Tool to retrieve list of users in MintHCM. Use this to get list of users in MintHCM and their details such as id, name, phone numbers, email, adress etc."
    )

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

                name = attributes["full_name"]

                phone_home = attributes["phone_home"]
                phone_mobile = attributes["phone_mobile"]
                phone_work = attributes["phone_work"]
                phone_other = attributes["phone_other"]

                address_street = attributes["address_street"]
                address_city = attributes["address_city"]
                address_state = attributes["address_state"]
                address_country = attributes["address_country"]
                address_postalcode = attributes["address_postalcode"]

                user_type = attributes["UserType"]
                employee_status = attributes["employee_status"]

                email_address = attributes["email_addresses_primary"]

                position = attributes["position_name"]
                reports_to_id = attributes["reports_to_id"]

                user_data = f"""ID: {user_id}, Imie i nazwisko: {name}, ID przełożonego: {reports_to_id}
                Telefon domowy: {phone_home}, Telefon komórkowy: {phone_mobile}, Telefon służbowy: {phone_work}, Telefon inny: {phone_other}, Email: {email_address},
                Adres: (ulica: {address_street}, miasto: {address_city}, województwo: {address_state}, kraj: {address_country}, kod pocztowy: {address_postalcode}),
                Typ użytkownika: {user_type},
                Status pracownika: {employee_status},
                Stanowisko: {position},
                """
                users.append(user_data)
            return users

        except Exception as e:
            return f"W trakcie pobierania użytkowników wystąpił błąd: {str(e)}"
