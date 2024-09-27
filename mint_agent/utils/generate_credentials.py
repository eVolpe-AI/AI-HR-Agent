import json
import os

from dotenv import load_dotenv
from pymongo import MongoClient


def generate_credentials():
    try:
        load_dotenv()

        db_uri = os.getenv("MONGO_URI")
        db_name = os.getenv("DB_NAME")

        current_dir = os.path.dirname(os.path.abspath(__file__))
        credential_path = os.path.join(current_dir, "../credentials.json")

        with open(credential_path, encoding="UTF-8") as f:
            credentials = json.load(f)

        client = MongoClient(db_uri)
        db = client[db_name]
        print(f"Generating credentials in {db_name} database")

        for user in credentials:
            collection_name = user["_id"]
            collection = db[collection_name]

            query = {"_id": user["_id"], "auth_token": user["auth_token"]}

            credentials_to_save = (
                user["user_credentials"] if "user_credentials" in user else {}
            )

            update = {"$set": {"user_credentials": credentials_to_save}}

            collection.update_one(query, update, upsert=True)
            print(f"Credentials generated for user: {user['_id']}")

        client.close()
    except Exception as e:
        print(f"Error while generating credentials: {e}")
