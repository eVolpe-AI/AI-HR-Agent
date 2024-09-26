import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()


class CredentialManager:
    """
    Manages credentials required for agent workflow.
    """

    def __init__(self):
        db_uri = os.getenv("MONGO_URI")
        db_name = os.getenv("DB_NAME")
        self.client = MongoClient(db_uri)
        self.db = self.client[db_name]

    def authenticate_user(self, user_id: str, token: str) -> bool:
        """
        Check if token exists in the database for the given user_id.

        Args:
            user_id (str): The ID of the user to authenticate.
            token (str): The authentication token for the user.

        Returns:
            bool: True if the user is authenticated, False otherwise.
        """
        collection = self.db[user_id]
        user = collection.find_one({"_id": user_id, "auth_token": token})
        return bool(user)

    def get_system_credentials(
        self, user_id: str, system: str, credential_type: str
    ) -> tuple:
        """
        Retrieve credentials for a given user, system, and credential type.

        Args:
            user_id (str): The ID of the user whose credentials are being retrieved.
            system (str): The system for which the credentials are needed.
            credential_type (str): The type of credentials required.

        Returns:
            tuple: A tuple containing appropriate credentials for the user, system
            and credential type or tuple of None if not found or error occurred.

        """
        try:
            match system:
                case "MintHCM":
                    if credential_type == "APIv8":
                        collection = self.db[user_id]
                    else:
                        raise ValueError(
                            f"Credential type '{credential_type}' not supported"
                        )

                    user_data = collection.find_one(
                        {
                            "user_credentials": {
                                "$elemMatch": {
                                    "system": system,
                                    "credential_type": credential_type,
                                }
                            }
                        },
                        {"user_credentials.$": 1},
                    )

                    if user_data and "user_credentials" in user_data:
                        credential = user_data["user_credentials"][0]
                        client_id = credential["credentials"]["client_id"]
                        secret = credential["credentials"]["secret"]
                        return client_id, secret
                    raise ValueError("Credentials not found")
                case _:
                    raise ValueError(f"System '{system}' not supported")
        except Exception:
            return None, None
