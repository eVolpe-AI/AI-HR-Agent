import os

from dotenv import load_dotenv
from loguru import logger
from pymongo import MongoClient

load_dotenv()


class CredentialManager:
    def __init__(self):
        db_uri = os.getenv("MONGO_URI")
        db_name = os.getenv("DB_NAME")
        self.client = MongoClient(db_uri)
        self.db = self.client[db_name]

    def authenticate_user(self, user, token):
        print(f"Trying to authenticate {user} with token {token}")
        collection = self.db[user]
        user = collection.find_one({"_id": user, "auth_token": token})

        if user:
            return True
        else:
            return False
