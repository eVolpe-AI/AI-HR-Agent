import atexit
import json
import math
import uuid
from typing import Union
from urllib.parse import quote

from oauthlib.oauth2 import (
    BackendApplicationClient,
    InvalidClientError,
    TokenExpiredError,
)
from oauthlib.oauth2.rfc6749.errors import CustomOAuth2Error
from requests_oauthlib import OAuth2Session

from mint_agent.utils.errors import AgentError


class SuiteCRM:
    def __init__(
        self, client_id: str, client_secret: str, url: str, logout_on_exit: bool = False
    ):
        self.baseurl = url
        self._client_id = client_id
        self._client_secret = client_secret
        self._logout_on_exit = logout_on_exit
        self._headers = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
        )
        self._login()
        self._modules()

    def _modules(self):
        self.Accounts = Module(self, "Accounts")
        self.Bugs = Module(self, "Bugs")
        self.Calendar = Module(self, "Calendar")
        self.Calls = Module(self, "Calls")
        self.Cases = Module(self, "Cases")
        self.Campaigns = Module(self, "Campaigns")
        self.Contacts = Module(self, "Contacts")
        self.Documents = Module(self, "Documents")
        self.Email = Module(self, "Email")
        self.Emails = Module(self, "Emails")
        self.Employees = Module(self, "Employees")
        self.Leads = Module(self, "Leads")
        self.Lists = Module(self, "Lists")
        self.Meetings = Module(self, "Meetings")
        self.Notes = Module(self, "Notes")
        self.Opportunities = Module(self, "Opportunities")
        self.Projects = Module(self, "Projects")
        self.Spots = Module(self, "Spots")
        self.Surveys = Module(self, "Surveys")
        self.Target = Module(self, "Target")
        self.Targets = Module(self, "Targets")
        self.Tasks = Module(self, "Tasks")
        self.Templates = Module(self, "Templates")
        self.Candidates = Module(self, "Candidates")

    def _refresh_token(self) -> None:
        """
        Fetch a new token from from token access url, specified in config file.
        :return: None
        """
        try:
            self.OAuth2Session.fetch_token(
                token_url=self.baseurl[:-2] + "access_token",
                client_id=self._client_id,
                client_secret=self._client_secret,
            )
        except InvalidClientError:
            raise AgentError("Invalid client id/secret")
        except CustomOAuth2Error:
            raise AgentError("Error while getting access to API")
        # Update configuration file with new token'
        with open("AccessToken.txt", "w+") as file:
            file.write(str(self.OAuth2Session.token))

    def _login(self) -> None:
        """
        Checks to see if a Oauth2 Session exists, if not builds a session and retrieves the token from the config file,
        if no token in config file, fetch a new one.

        :return: None
        """
        # Does session exist?
        if not hasattr(self, "OAuth2Session"):
            client = BackendApplicationClient(client_id=self._client_id)
            self.OAuth2Session = OAuth2Session(client=client, client_id=self._client_id)
            self.OAuth2Session.headers.update(
                {"User-Agent": self._headers, "Content-Type": "application/json"}
            )
            with open("AccessToken.txt", "w+") as file:
                token = file.read()
                if token == "":
                    self._refresh_token()
                else:
                    self.OAuth2Session.token = token
        else:
            self._refresh_token()

        # Logout on exit
        if self._logout_on_exit:
            atexit.register(self._logout)

    def _logout(self) -> None:
        """
        Logs out current Oauth2 Session
        :return: None
        """
        url = "/logout"
        self.request(f"{self.baseurl}{url}", "post")
        with open("AccessToken.txt", "w+") as file:
            file.write("")

    def request(self, url: str, method, parameters="") -> dict:
        """
        Makes a request to the given url with a specific method and data. If the request fails because the token expired
        the session will re-authenticate and attempt the request again with a new token.

        :param url: (string) The url
        :param method: (string) Get, Post, Patch, Delete
        :param parameters: (dictionary) Data to be posted

        :return: (dictionary) Data
        """

        url = quote(url, safe="/:?=&")
        data = json.dumps({"data": parameters})
        try:
            the_method = getattr(self.OAuth2Session, method)
        except AttributeError:
            return

        try:
            if parameters == "":
                data = the_method(url)
            else:
                data = the_method(url, data=data)
        except TokenExpiredError:
            self._refresh_token()
            if parameters == "":
                data = the_method(url)
            else:
                data = the_method(url, data=data)

        # Revoked Token
        attempts = 0
        while data.status_code == 401 and attempts < 1:
            self._refresh_token()
            if parameters == "":
                data = the_method(url)
            else:
                data = the_method(url, data=data)
            attempts += 1
        if data.status_code == 401:
            raise AgentError(
                "401 (Unauthorized) client id/secret has been revoked, new token was attempted and failed."
            )

        # Database Failure
        # SuiteCRM does not allow to query by a custom field see README, #Limitations
        if data.status_code == 400 and "Database failure." in data.content.decode():
            raise Exception(data.content.decode())

        # print(f"Data from request \n{data}")

        return json.loads(data.content)

    def verify_record_exists(self, record_id: str, module_name: str) -> bool:
        """
        Verifies if a record exists in the module.

        :param record_id: (string) id of the current module record.
        :param module_name: (string) the module name you want to search for the record in.

        :return: (boolean) True if the record exists, False if it does not.
        """
        url = f"/module/{module_name}/{record_id}"
        response = self.request(f"{self.baseurl}{url}", "get")
        errors = response.get("errors")
        if errors:
            if errors.get("status") == 400:
                return False
            raise Exception(errors)

        return True

    def get_record_url(
        self, module_name: str, record_id: str, return_name: bool = False
    ) -> Union[str, tuple[str, str]]:
        """
        Retrieves the URL of a specific record in the given module.

        :param module_name: (str) The name of the module containing the record.
        :param record_id: (str) The ID of the record in the module.
        :param return_name: (bool) If True, returns a tuple with the URL and the record name.
                            Defaults to False.

        :return:
            - If `return_name` is False: (str) The URL of the record.
            - If `return_name` is True: (Tuple[str, str]) A tuple containing:
                - (str) The URL of the record.
                - (str) The name of the record, or a truncated module name if the name is not available.
        """

        record = self.request(f"{self.baseurl}/module/{module_name}/{record_id}", "get")
        record_name = record.get("data", {}).get("attributes", {}).get("name", "")

        url = self.baseurl.split("/legacy")[0]
        if return_name:
            if record_name:
                return (
                    f"{url}/#/modules/{module_name}/DetailView/{record_id}",
                    record_name,
                )
            else:
                return (
                    f"{url}/#/modules/{module_name}/DetailView/{record_id}",
                    str(module_name)[:-1],
                )
        return f"{url}/#/modules/{module_name}/DetailView/{record_id}"

    def get_modules(self) -> list:
        """
        Gets all the modules that are available in the SuiteCRM.
        :return: (list) A list of all the modules.
        """
        url = "/meta/modules"
        module_response = self.request(f"{self.baseurl}{url}", "get")
        return list(module_response["data"]["attributes"].keys())

    def get_user_preferences(self, user_id: str) -> dict:
        """
        Gets the preferences of a user.

        :param user_id: (string) id of the user you want to get preferences for.

        :return: (dictionary) The preferences of the user.
        """
        url = f"/user-preferences/{user_id}"
        return self.request(f"{self.baseurl}{url}", "get")["data"]["attributes"][
            "global"
        ]


class Module:
    def __init__(self, suitecrm, module_name):
        self.module_name = module_name
        self.suitecrm = suitecrm

    def create(self, **attributes) -> dict:
        """
        Creates a record with given attributes
        :param attributes: (**kwargs) fields with data you want to populate the record with.

        :return: (dictionary) The record that was created with the attributes.
        """
        url = "/module"
        data = {
            "type": self.module_name,
            "id": str(uuid.uuid4()),
            "attributes": attributes,
        }
        return self.suitecrm.request(f"{self.suitecrm.baseurl}{url}", "post", data)

    def delete(self, record_id: str) -> dict:
        """
        Delete a specific record by id.
        :param record_id: (string) The record id within the module you want to delete.

        :return: (dictionary) Confirmation of deletion of record.
        """
        # Delete
        url = f"/module/{self.module_name}/{record_id}"
        return self.suitecrm.request(f"{self.suitecrm.baseurl}{url}", "delete")

    def fields(self) -> list:
        """
        Gets all the attributes that can be set in a record.
        :return: (list) All the names of attributes in a record.
        """
        # Get total record count
        url = f"/meta/fields/{self.module_name}"
        # Olka TODO
        result = self.suitecrm.request(f"{self.suitecrm.baseurl}{url}", "get")
        if "errors" in result:
            raise Exception(result["errors"])
        if "data" in result:
            attributes = result["data"]["attributes"]

            # attributes = {
            #    "attributes": {
            #        "id": {
            #            "vname": "LBL_ID",
            #            "type": "id",
            #            "required": "true",
            #            "dbType": "id"
            #        },
            #        "name": {
            #            "vname": "LBL_SUBJECT",
            #            "required": "true",
            #            "type": "name",
            #            "dbType": "varchar",
            #            "len": "255"
            #        },
            #    }
            # }
            # attributes is a list of dictionaries. We only need the keys and value of dbType
            # expected result:
            # attrs_shoprt = {
            #     "id": { "dbType": "id" },
            #     "name": { "dbType": "varchar" }
            # }
            attrs_short = {}
            for key, value in attributes.items():
                attrs_short[key] = {"dbType": value["dbType"]}
            # print(attrs_short)
            return attrs_short
            # return list(result['data'][0]['attributes'].keys())
        raise Exception(result)

    def get(
        self, fields: list = None, sort: str = None, operator: str = "and", **filters
    ) -> list:
        """
        Gets records given a specific id or filters, can be sorted only once, and the fields returned for each record
        can be specified.

        :param fields: (list) A list of fields you want to be returned from each record.
        :param sort: (string) The field you want the records to be sorted by.
        :param filters: (**kwargs) fields that the record has that you want to filter on.
                        ie... date_start= {'operator': '>', 'value':'2020-05-08T09:59:00+00:00'}

        Important notice: we don’t support multiple level sorting right now!

        :return: (list) A list of dictionaries, where each dictionary is a record.
        """
        # Fields Constructor
        if fields:
            fields = f"?fields[{self.module_name}]=" + ",".join(fields)
            url = f"/module/{self.module_name}{fields}&filter"
        else:
            url = f"/module/{self.module_name}?filter"
        if operator == "and" or operator == "or":
            url = f"{url}[operator]={operator}&filter"
        else:
            url = f"{url}[operator]=and&filter"  # Olka TODO

        # Filter Constructor
        operators = {
            "=": "EQ",
            "<>": "NEQ",
            ">": "GT",
            ">=": "GTE",
            "<": "LT",
            "<=": "LTE",
            "LIKE": "LIKE",
            "NOT LIKE": "NOT_IKE",
            "IN": "IN",
            "NOT IN": "NOT_IN",
        }
        for field, value in filters.items():
            if isinstance(value, dict):
                if value["operator"] == "BETWEEN":
                    # in value there are two values separated by comma
                    values = value["value"].split(",")
                    url = f'{url}[{field}][{operators[">"]}]= {values[0]}&'
                    url = f'{url}[{field}][{operators["<"]}]= {values[1]}&'

                else:
                    url = f'{url}[{field}][{operators[value["operator"]]}]={value["value"]}&'
            else:
                url = f"{url}[{field}][eq]={value}&"
        url = url[:-1]

        # Sort
        if sort:
            url = f"{url}&sort=-{sort}"

        # Execute
        result = self.suitecrm.request(f"{self.suitecrm.baseurl}{url}", "get")
        # TODO Olka
        if "data" in result:
            return result["data"]
        if "errors" in result:
            raise Exception(result["errors"])
        raise Exception(result["errors"])

    # TODO 1. Returns list of strings instead of dicts. 2. To check if its necessary to handle pagination
    # def get_all(self, record_per_page: int = 100) -> list:
    #     """
    #     Gets all the records in the module.
    #     :return: (list) A list of dictionaries, where each dictionary is a record.
    #              Will return all records within a module.
    #     """
    #     # Get total record count
    #     url = f"/module/{self.module_name}?page[number]=1&page[size]=1"
    #     pages = (
    #         math.ceil(
    #             self.suitecrm.request(f"{self.suitecrm.baseurl}{url}", "get")["meta"][
    #                 "total-pages"
    #             ]
    #             / record_per_page
    #         )
    #         + 1
    #     )
    #     result = []
    #     for page in range(1, pages):
    #         url = f"/module/{self.module_name}?page[number]={page}&page[size]={record_per_page}"
    #         result.extend(self.suitecrm.request(f"{self.suitecrm.baseurl}{url}", "get"))

    #     for record in result:
    #         print(type(record))
    #     return result

    def get_all(self) -> dict:
        url = f"/module/{self.module_name}"
        return self.suitecrm.request(f"{self.suitecrm.baseurl}{url}", "get")

    def update(self, record_id: str, **attributes) -> dict:
        """
        updates a record.

        :param record_id: (string) id of the current module record.
        :param attributes: (**kwargs) fields inside of the record to be updated.

        :return: (dictionary) The updated record
        """
        url = "/module"
        data = {"type": self.module_name, "id": record_id, "attributes": attributes}
        return self.suitecrm.request(f"{self.suitecrm.baseurl}{url}", "patch", data)

    def get_relationship(self, record_id: str, related_module_name: str) -> dict:
        """
        returns the relationship between this record and another module.

        :param record_id: (string) id of the current module record.
        :param related_module_name: (string) the module name you want to search relationships for, ie. Contacts.

        :return: (dictionary) A list of relationships that this module's record contains with the related module.
        """
        url = f"/module/{self.module_name}/{record_id}/relationships/{related_module_name.lower()}"
        return self.suitecrm.request(f"{self.suitecrm.baseurl}{url}", "get")

    def create_relationship(
        self, record_id: str, related_module_name: str, related_bean_id: str
    ) -> dict:
        """
        Creates a relationship between 2 records.

        :param record_id: (string) id of the current module record.
        :param related_module_name: (string) the module name of the record you want to create a relationship,
               ie. Contacts.
        :param related_bean_id: (string) id of the record inside of the other module.

        :return: (dictionary) A record that the relationship was created.
        """
        # Post
        url = f"/module/{self.module_name}/{record_id}/relationships"
        data = {"type": related_module_name.capitalize(), "id": related_bean_id}
        return self.suitecrm.request(f"{self.suitecrm.baseurl}{url}", "post", data)

    def delete_relationship(
        self, record_id: str, related_module_name: str, related_bean_id: str
    ) -> dict:
        """
        Deletes a relationship between 2 records.

        :param record_id: (string) id of the current module record.
        :param related_module_name: (string) the module name of the record you want to delete a relationship,
               ie. Contacts.
        :param related_bean_id: (string) id of the record inside of the other module.

        :return: (dictionary) A record that the relationship was deleted.
        """
        url = f"/module/{self.module_name}/{record_id}/relationships/{related_module_name.lower()}/{related_bean_id}"
        return self.suitecrm.request(f"{self.suitecrm.baseurl}{url}", "delete")
