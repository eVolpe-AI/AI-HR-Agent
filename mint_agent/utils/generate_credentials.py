import os

import inquirer
from cryptography.fernet import Fernet
from dotenv import load_dotenv, set_key
from pymongo import MongoClient
from termcolor import colored

load_dotenv()


def generate_encryption_key():
    key = os.getenv("FERNET_KEY")
    if key:
        print("Encryption key already exists in .env file")
        return
    key = Fernet.generate_key()
    set_key(".env", "FERNET_KEY", key.decode())
    print("Encryption key generated and saved to .env file")


def connect_to_db():
    try:
        db_uri = os.getenv("MONGO_URI")
        db_name = os.getenv("MONGO_DB_NAME")
        client = MongoClient(db_uri)
        db = client[db_name]
        return db
    except Exception as e:
        raise ConnectionError(f"Failed to connect to database: {e}")


def collect_user_data():
    KEY = os.getenv("FERNET_KEY").encode()
    user_id = inquirer.text(message="Enter user name")
    mint_user_id = inquirer.text(message="Enter user id from MintHCM")

    credentials = []
    add_credentials = inquirer.confirm(
        message=f"Add system credentials for {colored(user_id,"yellow")}?",
        default=False,
    )

    if add_credentials:
        client_id = inquirer.text(message="Enter API client_id")
        secret = inquirer.text(message="Enter API client secret")

        f = Fernet(KEY)
        secret = f.encrypt(secret.encode())

        credentials.append(
            {
                "system": "MintHCM",
                "credential_type": "APIv8",
                "credentials": {
                    "client_id": client_id,
                    "secret": secret,
                },
            }
        )

    return {
        "_id": user_id,
        "mint_user_id": mint_user_id,
        "user_credentials": credentials,
    }


def generate_credentials():
    db = connect_to_db()

    while True:
        user_data = collect_user_data()

        try:
            collection_name = user_data["_id"]
            collection = db[collection_name]
            query = {"_id": user_data["_id"], "mint_user_id": user_data["mint_user_id"]}

            credentials_to_save = (
                user_data["user_credentials"] if "user_credentials" in user_data else {}
            )

            update = {"$set": {"user_credentials": credentials_to_save}}
            collection.update_one(query, update, upsert=True)
            print(f"Credentials generated for user: {user_data['_id']}")
        except Exception as e:
            print(f"Error while generating credentials: {e}")

        add_more_users = inquirer.confirm(
            message="Add credentials for another user?", default=False
        )
        if not add_more_users:
            break

    db.client.close()
