import os
from datetime import datetime

import pytz
from dotenv import load_dotenv


def to_db_time(timestamp, format="%Y-%m-%d %H:%M:%S"):
    load_dotenv()
    try:
        user_timezone = pytz.timezone(os.getenv("USER_TIMEZONE"))
        db_timezone = pytz.timezone("UTC")

        if not user_timezone or not db_timezone:
            raise ValueError("USER_TIMEZONE and DB_TIMEZONE must be set in .env file")

        if isinstance(timestamp, str):
            timestamp = datetime.strptime(timestamp, format)

        timestamp = user_timezone.localize(timestamp)

        return timestamp.astimezone(db_timezone).strftime(format)
    except Exception as e:
        raise ValueError(f"Error converting time: {e}")
